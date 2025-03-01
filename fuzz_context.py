'''
Fuzz contexts - to conduct contextual testing of app
'''
import time
from typing import List, Union, Type
from adb_logcat import FatalWatcher

from emulator import Emulator
from adb_settings import AdbSettings
from adb_settings import UserRotation
from adb_settings import Airplane
from adb_settings import KeyEvent
import mutex
from telnet_connector import TelnetAdb
from telnet_connector import GsmProfile, NetworkDelay, NetworkStatus
import config_reader as config

from interval_event import IntervalEvent

import os
import secrets

dir = os.path.dirname(__file__)
StopFlagWatcher = os.path.join(dir, 'test/StopFlagWatcher')
ContextEventLog = os.path.join(dir, 'test/ContextEventLog')


PRINT_FLAG = True

EVENT_TYPES = Type[Union[GsmProfile, NetworkDelay,
                         NetworkStatus, Airplane, UserRotation, KeyEvent]]


class Fuzzer:

    '''
        Fuzzer Class
    '''
    # continue_airplane_fuzz = True
    # continue_rotation = True
    # continue_gsm_profile = True
    # continue_network_delay = True
    # continue_network_speed = True

    def __init__(self, interval_minimum: int,
                 interval_maximum: int,
                 seed: int, duration: int,
                 fatal_watcher: FatalWatcher,
                 uniform_interval: int = config.UNIFORM_INTERVAL)->None:
        '''
            `interval_minimum`, `interval_maximum`, `seed`, and `duration`
            are all integers.
            `interval_minimum`, `interval_maximum`, and `duration`
                are in seconds.
        '''
        if not isinstance(interval_minimum, int):
            raise ValueError("interval_minimum must be int")
        if not isinstance(interval_maximum, int):
            raise ValueError("interval_maximum must be int")
        if not isinstance(seed, int):
            raise ValueError("seed must be int")
        if not isinstance(duration, int):
            raise ValueError("duration must be int")
        if duration > 4200 or duration < 10:
            raise ValueError(
                "duration must be at least 10 seconds and at most 500 seconds")
        if seed > 500 or seed < 0:
            raise ValueError("seed must be within the range of 0 to 500")
        self.interval_maximum = interval_maximum
        self.interval_minimum = interval_minimum
        self.seed = seed
        self.duration = int(duration)
        self.uniform_interval = int(uniform_interval)
        self.fatal_watcher = fatal_watcher
        secrets.SystemRandom().seed(self.seed)
        # self.__setup_intervals(uniform_interval)
        # self.__setup_interval_events()

    # def __setup_intervals(self, uniform_interval: int=config.UNIFORM_INTERVAL): # noqa
    #     '''
    #     sets up intervals for event types. It configures:
    #     self.network_delay_interval,
    #     self.network_speed_interval,
    #     self.gsm_profile_interval,
    #     self.airplane_interval,
    #     self.rotation_interval
    #     '''
    #     self.network_delay_interval = self.duration_interval_steps_generator() # noqa
    #     self.network_speed_interval = self.duration_interval_steps_generator() # noqa
    #     self.gsm_profile_interval = self.uniform_duration_interval_steps_generator( # noqa
    #         int(uniform_interval))
    #     self.airplane_interval = self.duration_interval_steps_generator()
    #     self.rotation_interval = self.duration_interval_steps_generator()

    # def __setup_interval_events(self):
    #     '''
    #     sets up events for the following types:
    #     self.network_delay_events
    #     self.network_speed_events
    #     self.gsm_profile_events
    #     self.airplane_events
    #     self.rotation_events
    #     '''
    #     self.network_delay_events = self.event_per_step_generator(
    #         self.network_delay_interval, NetworkDelay)
    #     self.network_speed_events = self.event_per_step_generator(
    #         self.network_speed_interval, NetworkStatus)
    #     self.gsm_profile_events = self.event_per_step_generator(
    #         self.gsm_profile_interval, GsmProfile)
    #     self.airplane_events = self.event_per_step_generator(
    #         self.airplane_interval, Airplane)
    #     self.rotation_events = self.event_per_step_generator(
    #         self.rotation_interval, UserRotation)

    # def print_intervals_events(self):
    #     '''
    #         prints intervals with events
    #     '''
    #     print("Gsm profile interval: events")
    #     util.print_dual_list(self.gsm_profile_interval,
    #                          util.list_as_enum_name_list(self.gsm_profile_events, GsmProfile)) # noqa
    #     print("airplane interval: events")
    #     util.print_dual_list(self.airplane_interval, util.list_as_enum_name_list(# noqa
    #         self.airplane_events, Airplane))
    #     print("Network Delay interval: events")
    #     util.print_dual_list(self.network_delay_interval,
    #                          util.list_as_enum_name_list(self.network_delay_events, NetworkDelay))# noqa
    #     print("Rotation interval: events")
    #     util.print_dual_list(self.rotation_interval, util.list_as_enum_name_list(# noqa
    #         self.rotation_events, UserRotation))
    #     print("Network speed interval: events")
    #     util.print_dual_list(self.network_speed_interval, util.list_as_enum_name_list(# noqa
    #         self.network_speed_events, NetworkStatus))

    def __random_value_generator(self, lower_limit: int, upper_limit: int):

        if not isinstance(lower_limit, int):
            raise ValueError("lower_limit must be int")
        if not isinstance(upper_limit, int):
            raise ValueError("upper_limit must be int")
        return secrets.SystemRandom().randint(lower_limit, upper_limit)

    # def duration_interval_steps_generator(self)->List[int]:
    #     '''
    #         returns a List of duration event steps
    #     '''

    #     total_duration = self.duration
    #     cumulative_duration = 0
    #     intervals = []
    #     while True:
    #         interval_step = self.__random_value_generator(
    #             int(self.interval_minimum), int(self.interval_maximum))
    #         if (cumulative_duration + interval_step) < total_duration:
    #             cumulative_duration += interval_step
    #             intervals.append(interval_step)
    #         else:
    #             intervals.append(total_duration - cumulative_duration)
    #             break
    # self.intervals = intervals
    #     return intervals

    # def list_intervalevent_to_IntervalEvent(self,
    #                                         list_intervalevent: List[Tuple[int, EVENT_TYPES]],  # noqa
    #                                         event_type: EVENT_TYPES
    #                                         ) -> List[IntervalEvent]:
    #     # pylint: disable=invalid-name, E1126
    #     '''
    #     converts list to IntervalEvent type
    #     '''
    #     interval_events = []

    #     for i in range(0, len(list_intervalevent)):
    #         entity = IntervalEvent(
    #             i, list_intervalevent[i][0], list_intervalevent[i][1].name,
    #             event_type)
    #         interval_events.append(entity)
    #     return interval_events

    def generate_step_interval_event(self,
                                     event_type: EVENT_TYPES
                                     ) -> List[IntervalEvent]:
        '''
            returns a List of Interval_Event for each step
        '''

        total_duration = self.duration
        cumulative_duration = 0
        interval_events = []
        step = 0
        while True:
            interval = self.__random_value_generator(
                int(self.interval_minimum), int(self.interval_maximum))
            event = self.__random_value_generator(0, len(event_type) - 1)
            if (cumulative_duration + interval) < total_duration:
                cumulative_duration += interval

                interval_events.append(IntervalEvent(
                    step, interval, event_type(event).name, event_type))
                step += 1
            else:
                interval = total_duration - cumulative_duration
                interval_events.append(IntervalEvent(
                    step, interval, event_type(event).name, event_type))
                break
        return interval_events

    def generate_step_uniforminterval_event(self,
                                            event_type: EVENT_TYPES
                                            ) -> List[IntervalEvent]:
        '''
            returns a List of interval_event for each step
        '''

        cumulative_duration = 0
        interval_events = []
        step = 0
        while True:
            event = self.__random_value_generator(0, len(event_type) - 1)
            if cumulative_duration + self.uniform_interval < self.duration:
                cumulative_duration += self.uniform_interval
                interval_events.append(IntervalEvent(
                    step, self.uniform_interval,
                    event_type(event).name, event_type))
                step += 1
            else:
                interval_events.append(IntervalEvent(
                    step, self.duration - cumulative_duration,
                    event_type(event).name, event_type))
                break
        return interval_events

    # def uniform_duration_interval_steps_generator(self, uniform_interval: int)->List[int]: # noqa
    #     '''
    #         makes uniform interval steps by dividing `total_duration` with
    #         `uniform_interval`
    #     '''
    #     total_duration = self.duration
    #     intervals = []
    #     cumulative_duration = 0
    #     while True:
    #         if cumulative_duration + uniform_interval < total_duration:
    #             cumulative_duration += uniform_interval
    #             intervals.append(uniform_interval)
    #         else:
    #             intervals.append(total_duration - cumulative_duration)
    #             break
    #     return intervals

    # def event_per_step_generator(self,
    #                              intervals: List[int],
    #                              event_type: Union[GsmProfile, NetworkDelay, NetworkStatus])->\ # noqa
    #         List[Union[GsmProfile, NetworkDelay, NetworkStatus]]:
    #     event_types = []
    #     for dummy in intervals:
    #         event = self.__random_value_generator(
    #             0, len(event_type) - 1)
    #         event_types.append(event)
    #     return event_types

    # def __interval_event_execution(self, method_name, event_type: str,
    #                                intervals, events, enum_type: enum):
    #     for i in range(0, len(intervals) - 1):
    #         if PRINT_FLAG:
    #             print("{} - {}: {}".format(event_type,
    #                                        intervals[i], enum_type(events[i]).name))# noqa
    #         method_name(enum_type(events[i]))
    #         time.sleep(intervals[i])

    def __execute_interval_event(self, method_name,
                                 interval_events: List[IntervalEvent]):
        # util.debug_print("Execution: ", interval_events, flag=PRINT_FLAG)

        # file = open('test/StopFlagWatcher', 'r')
        file = open(StopFlagWatcher, 'r')
        for interval_event in interval_events:

            if "1" in file.readline(1):
                print("Contextual event finished")
                break

            if self.fatal_watcher.has_fatal_exception_watch():
                print("Fatal Exception Detected. Breaking from " +
                      interval_event.event_type.__name__)
                break

            # if self.fatal_exception:
            #     print("fatal crash. Stopping " +
            #           interval_event.event_type.__name__)
            #     break
            # util.debug_print(interval_event, flag=PRINT_FLAG)

            print(interval_event)

            # file2 = open("test/ContextEventLog", 'r')
            file2 = open(ContextEventLog, 'r')
            filedata = file2.read()

            # file2 = open("test/ContextEventLog", "w")
            file2 = open(ContextEventLog, 'w')
            if len(filedata) < 10:
                file2.write(IntervalEvent.__str__(interval_event))
            else:
                file2.write(filedata + "\n" +
                            IntervalEvent.__str__(interval_event))

            file2.close()

            method_name(interval_event.event_type[interval_event.event])
            time.sleep(interval_event.interval)
            # for i in range(0, len(intervals) - 1):
            #     if PRINT_FLAG:
            #         print("{} - {}: {}".format(event_type,
            #                                    intervals[i], enum_type(events[i]).name))# noqa
            #     method_name(enum_type(events[i]))
            #     time.sleep(intervals[i])

    def random_airplane_mode_call(self, adb_device: str,
                                  interval_events: List[IntervalEvent] = None):
        '''
        randomly fuzzes airplane_mode_call for the specified
        running virtual device identified by `adb_device`
        '''
        device = AdbSettings(adb_device)
        if interval_events is None:
            interval_events = self.generate_step_interval_event(Airplane)
        # util.debug_print(interval_events, flag=PRINT_FLAG)
        self.__execute_interval_event(
            device.set_airplane_mode, interval_events)
        # self.__interval_event_execution(
        #     device.set_airplane_mode, "airplane_mode",
        #     self.airplane_interval, self.airplane_events, Airplane)

        # device.set_airplane_mode(Airplane.MODE_OFF)

    def random_key_event(self, adb_device: str,
                         interval_events: List[IntervalEvent]=None):
        '''
            random fuzz of random key events
            and KeyEvent type IntervalEvent
        '''
        device = AdbSettings(adb_device)
        if interval_events is None:
            interval_events = self.generate_step_interval_event(KeyEvent)
        self.__execute_interval_event(
            device.adb_send_key_event, interval_events)

    def random_rotation(self, adb_device: str,
                        interval_events: List[IntervalEvent] = None):
        '''
        randomly fuzzes airplane_mode_call for the specified
        running virtual device identified by `adb_device`
        and UserRotation type IntervalEvent
        '''
        device = AdbSettings(adb_device)
        if interval_events is None:
            interval_events = self.generate_step_interval_event(UserRotation)
        # self.__interval_event_execution(
        #     device.set_user_rotation, "rotation_mode",
        #     self.rotation_interval, self.rotation_events, UserRotation)
        # util.debug_print(interval_events, flag=PRINT_FLAG)

        # self.__execute_interval_event(
        #     device.set_user_rotation, interval_events)
        # device.set_user_rotation(UserRotation.ROTATION_POTRAIT)
        # file = open('test/StopFlagWatcher', 'r')
        file = open(StopFlagWatcher, 'r')
        for interval_event in interval_events:

            if "1" in file.readline(1):
                print("Contextual event finished")
                break

            if self.fatal_watcher.has_fatal_exception_watch():
                print("Fatal Exception Detected. Breaking from " +
                      interval_event.event_type.__name__)
                break

            # if self.fatal_exception:
            #     print("fatal crash. Stopping " +
            #           interval_event.event_type.__name__)
            #     break
            # util.debug_print(interval_event, flag=PRINT_FLAG)

            print(interval_event)

            file2 = open(ContextEventLog, 'r')
            filedata = file2.read()

            file2 = open(ContextEventLog, "w")

            if len(filedata) < 10:
                file2.write(IntervalEvent.__str__(interval_event))
            else:
                file2.write(filedata + "\n" +
                            IntervalEvent.__str__(interval_event))

            file2.close()

            device.set_user_rotation(
                interval_event.event_type[interval_event.event])
            print("testing rotation manual service")
            mutex.ROTATION_MUTEX = 1
            print("ROTATION_MUTEX set to 1 for forcing update")
            time.sleep(interval_event.interval)

        # device.set_user_rotation(UserRotation.ROTATION_POTRAIT)

    def random_network_speed(self, host: str, emulator: Emulator,
                             interval_events: List[IntervalEvent]=None):
        '''
        randomly fuzzes network speed by `TelnetAdb(host, port)` type object
        and NetworkStatus type IntervalEvent
        '''
        telnet_obj = TelnetAdb(host, emulator.port)

        if interval_events is None:
            interval_events = self.generate_step_interval_event(NetworkStatus)
        # util.debug_print(interval_events, flag=PRINT_FLAG)
        # self.__interval_event_execution(
        #     telnet_obj.set_connection_speed, "network_speed",
        # self.network_speed_interval, self.network_speed_events,
        # NetworkStatus)
        self.__execute_interval_event(
            telnet_obj.set_connection_speed, interval_events)

        # telnet_obj.reset_network_speed()

    def random_network_delay(self, host: str, emulator: Emulator,
                             interval_events: List[IntervalEvent]=None):
        '''
        randomly fuzzes network delay by `TelnetAdb(host, port)` type object
        and NetworkDelay type IntervalEvent
        '''

        telnet_obj = TelnetAdb(host, emulator.port)
        if interval_events is None:
            interval_events = self.generate_step_interval_event(NetworkDelay)
        # util.debug_print(interval_events, flag=PRINT_FLAG)
        self.__execute_interval_event(
            telnet_obj.set_connection_delay, interval_events)
        # self.__interval_event_execution(
        #     telnet_obj.set_connection_delay, "connection_delay",
        # self.network_delay_interval, self.network_delay_events, NetworkDelay)
        # telnet_obj.reset_network_delay()

    def random_gsm_profile(self, host: str, emulator: Emulator,
                           uniform_interval: int,
                           interval_events: List[IntervalEvent]=None):
        '''
        randomly fuzzes gsm_profile by `TelnetAdb(host, port)` type object
        and GsmProfile type IntervalEvent
        '''
        if uniform_interval >= self.duration:
            raise ValueError(
                "uniform interval must be smaller than total duration")
        if interval_events is None:
            interval_events = self.generate_step_uniforminterval_event(
                GsmProfile)
        telnet_obj = TelnetAdb(host, emulator.port)
        # self.__interval_event_execution(
        #     telnet_obj.set_gsm_profile, "gsm_profile",
        #     self.gsm_profile_interval, self.gsm_profile_events, GsmProfile)
        # util.debug_print(interval_events, flag=PRINT_FLAG)
        self.__execute_interval_event(
            telnet_obj.set_gsm_profile, interval_events)
        # telnet_obj.reset_gsm_profile()

    def reset_adb(self, adb_device):
        '''
            resets to default for adb_device
        '''
        device = AdbSettings(adb_device)
        device.reset_all()

    def reset_telnet_obj(self, host: str, emulator: Emulator):
        """
        resets the emulator for telnet specific contexts
        """
        telnet_obj = TelnetAdb(host, emulator.port)
        telnet_obj.reset_all()
