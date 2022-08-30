import click
import time
from threading import Timer
import plotext as plt
import os

from .loadstar_sensors_interface import LoadstarSensorsInterface, ScaleFactor


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.command(context_settings=CONTEXT_SETTINGS,
               no_args_is_help=True)
@click.option('-p','--port',
              default=None,
              help='Device name (e.g. /dev/ttyUSB0 on GNU/Linux or COM3 on Windows)')
@click.option('-i','--info',
              is_flag=True,
              default=False,
              help='Print the device info and exit')
@click.option('-T','--tare',
              is_flag=True,
              default=False,
              help='Tare before getting sensor values.')
@click.option('-s','--scale-factor',
              type=click.Choice(list([sf.name for sf in ScaleFactor]),
                                case_sensitive=False),
              default=ScaleFactor.ONE.name,
              show_default=True,
              help='Scale output values (e.g. to convert units)')
@click.option('-w','--window',
              default=1,
              show_default=True,
              help='Number of points to average. (1-1024 samples).')
@click.option('-t','--threshold',
              default=25,
              show_default=True,
              help='Percentage of capacity below which average is performed. (1-100%).')
@click.option('-f','--frequency',
              default=1,
              show_default=True,
              help='Frequency of sensor value measurements in Hz.')
@click.option('-d','--duration',
              default=10,
              show_default=True,
              help='Duration of sensor value measurements in seconds.')
def main(port,
         info,
         tare,
         scale_factor,
         window,
         threshold,
         frequency,
         duration):
    dev = LoadstarSensorsInterface(port=port)
    dev.set_scale_factor(scale_factor)
    dev.set_averaging_window(window)
    dev.set_averaging_threshold(threshold)

    clear_screen()
    dev.print_device_info({'measurement_frequency': frequency,
                           'measurement_duration': duration})
    if info:
        return

    if tare:
        input_value = input('Press Enter to tare and then continue or q then Enter to quit...\n')
    else:
        input_value = input('Press Enter to continue or q then Enter to quit...\n')
    if (input_value == 'q'):
        return

    if tare:
        print('taring...')
        dev.tare()
        time.sleep(2)

    clear_screen()

    max_value = dev.get_load_capacity()
    loadstar_sensors_plotter = LoadstarSensorsPlotter(dev,frequency,duration,max_value)
    loadstar_sensors_plotter.plot()

def clear_screen():
    if (os.name == 'posix'):
        os.system('clear')
    else:
        os.system('cls')

class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)

class LoadstarSensorsPlotter():
    def __init__(self,
                 device,
                 frequency,
                 duration,
                 max_value):
        self._device = device
        self._interval = 1.0 / frequency
        self._datum_count = frequency * duration
        self._max_value = max_value
        self._timer = RepeatTimer(self._interval,self._draw)
        self._plotting = False

    def plot(self):
        self._data = [0 for i in range(0,self._datum_count)]
        self._datum_index = 0
        self._plotting = True
        self._time_start = None
        self._timer.start()
        while self._plotting:
            time.sleep(self._interval)
        self._timer.cancel()

    def _draw(self):
        if not self._time_start:
            self._time_start = time.time()
        if self._datum_index >= self._datum_count:
            self._plotting = False
            return
        t = time.time() - self._time_start
        sensor_value = self._device.get_sensor_value()
        # self._data[self._datum_index] = sensor_value
        self._datum_index += 1
        print(f'time: {t:.1f}, datum_count: {self._datum_index}, sensor_value: {sensor_value}')
        # plt.clt()
        # plt.cld()
        # plt.title(f'Sensor Values time: {t:.1f}, datum_count: {self._datum_index}')
        # plt.ylim(0,self._max_value)
        # plt.plot(self._data)

        # plt.sleep(0.001)
        # plt.show()

if __name__ == '__main__':
    main()
