#!/usr/bin/env python3
"""227 当 BLE 外设(GATT 服务器) —— Nordic UART Service 透传,免配对。
板子(BLE 主机)连上后:订阅 TX(收 227 推的数据)、写 RX(把数据发给 227)。
依赖:python3-dbus + python3-gi(已确认在 227 上)。
"""
import dbus, dbus.mainloop.glib, dbus.service
from gi.repository import GLib

BLUEZ = 'org.bluez'
OM = 'org.freedesktop.DBus.ObjectManager'
PROP = 'org.freedesktop.DBus.Properties'
GATT_MGR = 'org.bluez.GattManager1'
ADV_MGR = 'org.bluez.LEAdvertisingManager1'
SVC_IFACE = 'org.bluez.GattService1'
CHR_IFACE = 'org.bluez.GattCharacteristic1'
ADV_IFACE = 'org.bluez.LEAdvertisement1'

NUS = '6e400001-b5a3-f393-e0a9-e50e24dcca9e'   # 服务
RX  = '6e400002-b5a3-f393-e0a9-e50e24dcca9e'   # 板子写→227(write)
TX  = '6e400003-b5a3-f393-e0a9-e50e24dcca9e'   # 227 推→板子(notify)


class App(dbus.service.Object):
    def __init__(self, bus):
        self.path = '/com/gwpeer'
        dbus.service.Object.__init__(self, bus, self.path)
        self.svc = Service(bus, 0)
        self.tx = Char(bus, 0, TX, ['notify'], self.svc)
        self.rx = RxChar(bus, 1, RX, ['write', 'write-without-response'], self.svc, self.tx)
        self.svc.chars = [self.tx, self.rx]

    def get_path(self): return dbus.ObjectPath(self.path)

    @dbus.service.method(OM, out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        r = {self.svc.get_path(): self.svc.get_properties()}
        for c in self.svc.chars:
            r[c.get_path()] = c.get_properties()
        return r


class Service(dbus.service.Object):
    def __init__(self, bus, idx):
        self.path = '/com/gwpeer/svc%d' % idx
        self.chars = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_path(self): return dbus.ObjectPath(self.path)

    def get_properties(self):
        return {SVC_IFACE: {
            'UUID': NUS, 'Primary': dbus.Boolean(True),
            'Characteristics': dbus.Array([c.get_path() for c in self.chars], signature='o')}}

    @dbus.service.method(PROP, in_signature='s', out_signature='a{sv}')
    def GetAll(self, iface): return self.get_properties()[SVC_IFACE]

    @dbus.service.method(PROP, in_signature='ss', out_signature='v')
    def Get(self, iface, name):
        return self.get_properties()[SVC_IFACE][name]


class Char(dbus.service.Object):
    def __init__(self, bus, idx, uuid, flags, svc):
        self.path = svc.path + '/chr%d' % idx
        self.uuid, self.flags, self.svc = uuid, flags, svc
        self.notifying = False
        dbus.service.Object.__init__(self, bus, self.path)

    def get_path(self): return dbus.ObjectPath(self.path)

    def get_properties(self):
        return {CHR_IFACE: {'Service': self.svc.get_path(), 'UUID': self.uuid,
                            'Flags': dbus.Array(self.flags, signature='s')}}

    @dbus.service.method(PROP, in_signature='s', out_signature='a{sv}')
    def GetAll(self, iface): return self.get_properties()[CHR_IFACE]

    @dbus.service.method(PROP, in_signature='ss', out_signature='v')
    def Get(self, iface, name):
        return self.get_properties()[CHR_IFACE][name]

    @dbus.service.signal(PROP, signature='sa{sv}as')
    def PropertiesChanged(self, iface, changed, inval): pass

    @dbus.service.method(CHR_IFACE)
    def StartNotify(self):
        self.notifying = True
        print('[227] 板子已订阅 TX,开始能收到推送', flush=True)

    @dbus.service.method(CHR_IFACE)
    def StopNotify(self):
        self.notifying = False

    def send(self, text):
        if not self.notifying:
            return
        val = dbus.Array([dbus.Byte(b) for b in text.encode()], signature='y')
        self.PropertiesChanged(CHR_IFACE, {'Value': val}, [])
        print('[227→板子] %s' % text, flush=True)


class RxChar(Char):
    def __init__(self, bus, idx, uuid, flags, svc, tx):
        Char.__init__(self, bus, idx, uuid, flags, svc)
        self.tx = tx

    @dbus.service.method(CHR_IFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        data = bytes(value)
        print('[板子→227] %r' % data, flush=True)
        self.tx.send('echo:' + data.decode('utf-8', 'replace'))   # 收到就回一条,证明双向


class Advertisement(dbus.service.Object):
    def __init__(self, bus):
        self.path = '/com/gwpeer/adv0'
        dbus.service.Object.__init__(self, bus, self.path)

    def get_path(self): return dbus.ObjectPath(self.path)

    @dbus.service.method(PROP, in_signature='s', out_signature='a{sv}')
    def GetAll(self, iface):
        # 只放名字:128位UUID(18B)+名字+TxPower 会超过31字节上限导致广播起不来。
        # 板子连上后再发现 NUS 服务即可。
        return {'Type': dbus.String('peripheral'),
                'Discoverable': dbus.Boolean(True),
                'LocalName': dbus.String('GW-PEER')}

    @dbus.service.method(PROP, in_signature='ss', out_signature='v')
    def Get(self, iface, name):
        return self.GetAll(iface)[name]

    @dbus.service.method(ADV_IFACE)
    def Release(self): pass


def find_adapter(bus):
    om = dbus.Interface(bus.get_object(BLUEZ, '/'), OM)
    for path, ifaces in om.GetManagedObjects().items():
        if GATT_MGR in ifaces:
            return path
    return None


def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    adapter = find_adapter(bus)
    if not adapter:
        print('找不到蓝牙适配器'); return
    props = dbus.Interface(bus.get_object(BLUEZ, adapter), PROP)
    props.Set('org.bluez.Adapter1', 'Powered', dbus.Boolean(True))
    props.Set('org.bluez.Adapter1', 'DiscoverableTimeout', dbus.UInt32(0))
    props.Set('org.bluez.Adapter1', 'Discoverable', dbus.Boolean(True))

    app = App(bus)
    adv = Advertisement(bus)
    gm = dbus.Interface(bus.get_object(BLUEZ, adapter), GATT_MGR)
    am = dbus.Interface(bus.get_object(BLUEZ, adapter), ADV_MGR)

    loop = GLib.MainLoop()
    gm.RegisterApplication(app.get_path(), {},
        reply_handler=lambda: print('[227] GATT 服务已注册', flush=True),
        error_handler=lambda e: print('注册服务失败:', e, flush=True))
    am.RegisterAdvertisement(adv.get_path(), {},
        reply_handler=lambda: print('[227] 广播已开,名字 GW-PEER,等板子连…', flush=True),
        error_handler=lambda e: print('广播失败:', e, flush=True))

    # 每 5 秒主动推一条,验证"227→板子"方向(板子订阅后能收到)
    n = [0]
    def heartbeat():
        n[0] += 1
        app.tx.send('hello-from-227 #%d' % n[0])
        return True
    GLib.timeout_add_seconds(5, heartbeat)

    print('[227] BLE 外设运行中,Ctrl-C 退出', flush=True)
    try:
        loop.run()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
