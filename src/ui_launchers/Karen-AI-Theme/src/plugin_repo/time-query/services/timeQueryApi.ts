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
    return this.api.execute({ mode }) as Promise<CurrentTimeResponse>;
  }

  async getWorldTime(query: string, timezone?: string): Promise<WorldTimeResponse> {
    return this.api.execute({ mode: 'world_time', query, timezone }) as Promise<WorldTimeResponse>;
  }

  async resolveMultiClocks(clocks: string[]): Promise<MultiClockResolveResponse> {
    return this.api.execute({ mode: 'multi_clock', action: 'resolve', clocks }) as Promise<MultiClockResolveResponse>;
  }

  async listMultiClocks(): Promise<MultiClockListResponse> {
    return this.api.execute({ mode: 'multi_clock', action: 'list' }) as Promise<MultiClockListResponse>;
  }

  async addMultiClock(timezone: string): Promise<BaseResponse> {
    return this.api.execute({ mode: 'multi_clock', action: 'add', timezone }) as Promise<BaseResponse>;
  }

  async removeMultiClock(clock_id: string): Promise<BaseResponse> {
    return this.api.execute({ mode: 'multi_clock', action: 'remove', clock_id }) as Promise<BaseResponse>;
  }

  async setStopwatchAction(action: string, stopwatch_id: string = 'default'): Promise<StopwatchResponse> {
    return this.api.execute({ mode: 'stopwatch', action, stopwatch_id }) as Promise<StopwatchResponse>;
  }

  async getAlarms(): Promise<AlarmListResponse> {
    return this.api.execute({ mode: 'alarm', action: 'list' }) as Promise<AlarmListResponse>;
  }

  async createAlarm(data: AlarmCreateParams): Promise<AlarmResponse> {
    return this.api.execute({ mode: 'alarm', action: 'create', ...data }) as Promise<AlarmResponse>;
  }

  async updateAlarm(alarm_id: string, data: AlarmUpdateParams): Promise<AlarmResponse> {
    return this.api.execute({ mode: 'alarm', action: 'update', alarm_id, ...data }) as Promise<AlarmResponse>;
  }

  async deleteAlarm(alarm_id: string): Promise<BaseResponse> {
    return this.api.execute({ mode: 'alarm', action: 'delete', alarm_id }) as Promise<BaseResponse>;
  }

  async setAlarmStatus(alarm_id: string, enabled: boolean): Promise<AlarmResponse> {
    return this.api.execute({ mode: 'alarm', action: enabled ? 'enable' : 'disable', alarm_id }) as Promise<AlarmResponse>;
  }

  async convertTimezone(datetime: string, from_timezone: string, to_timezone: string): Promise<ConversionResponse> {
    return this.api.execute({ mode: 'convert_timezone', datetime, from_timezone, to_timezone }) as Promise<ConversionResponse>;
  }
}
