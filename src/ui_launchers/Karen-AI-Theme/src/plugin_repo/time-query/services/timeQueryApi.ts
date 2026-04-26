import { ExtensionAPI } from '@/lib/extensions/hooks/usePluginExtension';
import type { AlarmCreateParams, AlarmUpdateParams, TimePayload, ClockItem, StopwatchState, AlarmItem, TimezoneConversionResult } from '../types';

interface BaseResponse {
  status: string;
  mode: string;
  error?: string;
}

interface CurrentTimeResponse extends BaseResponse, TimePayload {}
interface WorldTimeResponse extends BaseResponse, TimePayload {}
interface MultiClockListResponse extends BaseResponse { clocks: ClockItem[] }
interface MultiClockResolveResponse extends BaseResponse { clocks: ClockItem[] }
interface StopwatchResponse extends BaseResponse { stopwatch: StopwatchState }
interface AlarmListResponse extends BaseResponse { alarms: AlarmItem[] }
interface AlarmResponse extends BaseResponse { alarm: AlarmItem }
interface ConversionResponse extends BaseResponse, TimezoneConversionResult {}

export class TimeQueryApi {
  private api: ExtensionAPI;

  constructor(api: ExtensionAPI) {
    this.api = api;
  }

  async getCurrentTime(mode: string = 'datetime'): Promise<CurrentTimeResponse> {
    return this.api.execute({ mode });
  }

  async getWorldTime(query: string, timezone?: string): Promise<WorldTimeResponse> {
    return this.api.execute({ mode: 'world_time', query, timezone });
  }

  async resolveMultiClocks(clocks: string[]): Promise<MultiClockResolveResponse> {
    return this.api.execute({ mode: 'multi_clock', action: 'resolve', clocks });
  }

  async listMultiClocks(): Promise<MultiClockListResponse> {
    return this.api.execute({ mode: 'multi_clock', action: 'list' });
  }

  async addMultiClock(timezone: string): Promise<BaseResponse> {
    return this.api.execute({ mode: 'multi_clock', action: 'add', timezone });
  }

  async removeMultiClock(clock_id: string): Promise<BaseResponse> {
    return this.api.execute({ mode: 'multi_clock', action: 'remove', clock_id });
  }

  async setStopwatchAction(action: string, stopwatch_id: string = 'default'): Promise<StopwatchResponse> {
    return this.api.execute({ mode: 'stopwatch', action, stopwatch_id });
  }

  async getAlarms(): Promise<AlarmListResponse> {
    return this.api.execute({ mode: 'alarm', action: 'list' });
  }

  async createAlarm(data: AlarmCreateParams): Promise<AlarmResponse> {
    return this.api.execute({ mode: 'alarm', action: 'create', ...data });
  }

  async updateAlarm(alarm_id: string, data: AlarmUpdateParams): Promise<AlarmResponse> {
    return this.api.execute({ mode: 'alarm', action: 'update', alarm_id, ...data });
  }

  async deleteAlarm(alarm_id: string): Promise<BaseResponse> {
    return this.api.execute({ mode: 'alarm', action: 'delete', alarm_id });
  }

  async setAlarmStatus(alarm_id: string, enabled: boolean): Promise<AlarmResponse> {
    return this.api.execute({ mode: 'alarm', action: enabled ? 'enable' : 'disable', alarm_id });
  }

  async convertTimezone(datetime: string, from_timezone: string, to_timezone: string): Promise<ConversionResponse> {
    return this.api.execute({ mode: 'convert_timezone', datetime, from_timezone, to_timezone });
  }
}
