from libdaq2.libdaq2 import *


def main():
    libdaq2_init()
    try:
        count = libdaq2_device_get_count()
        print(f"device_count={count}")
        if count <= 0:
            return

        sn = libdaq2_device_get_sn(0)
        dev = DAQ4211(sn)
        dev.device_open()
        try:
            print(f"sn={sn}")
            print(f"name={dev.device_get_name()}")
            print(f"model={dev.device_get_model()}")

            dev.ADC.set_propertyInt(b"InputRange", 0)  # +/-10V
            dev.ADC.set_propertyString(b"SampleMode", b"OneShot")
            dev.ADC.set_propertyInt(b"Channels", 8)
            dev.ADC.sync_channelsetting()
            values = dev.ADC.single_Sample(8)
            for index, value in enumerate(values):
                print(f"AI{index}={value:.6f}V")

            dev.DIO.set_propertyInt(b"DIO0_Mode", IO_MODE_IN)
            dev.DIO.set_propertyInt(b"DIO1_Mode", IO_MODE_IN)
            dev.DIO.set_propertyInt(b"DIO2_Mode", IO_MODE_IN)
            dev.DIO.set_propertyInt(b"DIO3_Mode", IO_MODE_IN)
            print(f"DI={dev.DIO.read_port()}")
        finally:
            dev.device_close()
    finally:
        libdaq2_exit()


if __name__ == "__main__":
    main()
