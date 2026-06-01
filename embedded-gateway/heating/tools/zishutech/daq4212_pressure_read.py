import argparse
import time

from libdaq2.libdaq2 import *


def to_pressure(voltage, v_min, v_max, p_min, p_max):
    if v_max == v_min:
        raise ValueError("v_max must not equal v_min")
    ratio = (voltage - v_min) / (v_max - v_min)
    return p_min + ratio * (p_max - p_min)


def main():
    parser = argparse.ArgumentParser(description="Read DAQ-4212 AI voltage and convert it to pressure.")
    parser.add_argument("--channel", type=int, default=0, help="AI channel index, 0-7")
    parser.add_argument("--v-min", type=float, default=0.0, help="Sensor low voltage, for example 0, 0.5, or 1")
    parser.add_argument("--v-max", type=float, default=10.0, help="Sensor high voltage, for example 5 or 10")
    parser.add_argument("--p-min", type=float, default=0.0, help="Pressure at v-min")
    parser.add_argument("--p-max", type=float, default=1.6, help="Pressure at v-max")
    parser.add_argument("--unit", default="MPa", help="Pressure unit label")
    parser.add_argument("--interval", type=float, default=1.0, help="Read interval seconds")
    parser.add_argument("--count", type=int, default=0, help="Read count, 0 means forever")
    args = parser.parse_args()

    if args.channel < 0 or args.channel > 7:
        raise ValueError("--channel must be 0-7")

    libdaq2_init()
    try:
        device_count = libdaq2_device_get_count()
        print(f"device_count={device_count}")
        if device_count <= 0:
            return

        sn = libdaq2_device_get_sn(0)
        dev = DAQ4211(sn)
        dev.device_open()
        try:
            print(f"sn={sn}")
            print(f"name={dev.device_get_name()}")
            print(f"model={dev.device_get_model()}")
            print(
                "mapping=AI{ch}: {v_min:g}-{v_max:g}V -> {p_min:g}-{p_max:g}{unit}".format(
                    ch=args.channel,
                    v_min=args.v_min,
                    v_max=args.v_max,
                    p_min=args.p_min,
                    p_max=args.p_max,
                    unit=args.unit,
                )
            )

            dev.ADC.set_propertyInt(b"InputRange", 0)  # +/-10V
            dev.ADC.set_propertyString(b"SampleMode", b"OneShot")
            dev.ADC.set_propertyInt(b"Channels", 8)
            dev.ADC.sync_channelsetting()

            index = 0
            while args.count == 0 or index < args.count:
                values = dev.ADC.single_Sample(8)
                voltage = values[args.channel]
                pressure = to_pressure(voltage, args.v_min, args.v_max, args.p_min, args.p_max)
                print(
                    "AI{ch}={voltage:.6f}V pressure={pressure:.6f}{unit} all_ai=[{all_ai}]".format(
                        ch=args.channel,
                        voltage=voltage,
                        pressure=pressure,
                        unit=args.unit,
                        all_ai=", ".join(f"{value:.6f}" for value in values),
                    )
                )
                index += 1
                if args.count == 0 or index < args.count:
                    time.sleep(args.interval)
        finally:
            dev.device_close()
    finally:
        libdaq2_exit()


if __name__ == "__main__":
    main()
