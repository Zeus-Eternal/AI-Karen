'use server';
/**
 * @fileOverview Enhanced core tool functions for AI Karen integration.
 * These functions integrate with AI Karen's backend plugin system.
 */

import type { TemperatureUnit, WeatherServiceOption } from '@/lib/types';
import { getKarenBackend } from '@/lib/karen-backend';

/* ----------------------------- Date / Time ----------------------------- */

export async function getCurrentDate(): Promise<string> {
  return new Date().toLocaleDateString(undefined, {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

export async function getCurrentTime(location?: string): Promise<string> {
  const originalLocation = location?.trim();
  const logs: string[] = [];
  logs.push(`getCurrentTime called with location: "${originalLocation || 'none'}"`);

  // Helper to pretty-print logs on success/fail
  const flush = () => console.log(logs.join('\n'));

  if (originalLocation) {
    // Attempt 1: timeapi.io (Primary Source)
    const timeApiLocation = originalLocation.replace(/, /g, '/').replace(/ /g, '_');
    const timeApiUrl = `https://timeapi.io/api/Time/current/zone?timeZone=${encodeURIComponent(
      timeApiLocation
    )}`;
    logs.push(`getCurrentTime: Attempt 1 (timeapi.io): ${timeApiUrl}`);

    try {
      const response = await fetch(timeApiUrl);
      const responseText = await response.text();
      logs.push(
        `getCurrentTime: timeapi.io response status: ${response.status}, body: ${responseText.substring(
          0,
          200
        )}`
      );

      if (!response.ok) {
        let errorDetail = `TimeAPI.io error: Status ${response.status}.`;
        try {
          const errorData = JSON.parse(responseText);
          if (errorData && (errorData.message || errorData.Message)) {
            errorDetail += ` Message: ${errorData.message || errorData.Message}`;
          }
          if (responseText.toLowerCase().includes('not found') || responseText.toLowerCase().includes('invalid timezone')) {
            errorDetail += ` Location "${timeApiLocation}" likely not recognized by timeapi.io. It often requires "Region/City" format (e.g., America/New_York).`;
          }
        } catch {
          /* non-JSON body */
        }
        throw new Error(errorDetail);
      }

      const data = JSON.parse(responseText) as { dateTime?: string; timeZone?: string };
      if (data?.dateTime && data?.timeZone) {
        const timeInLocation = new Date(data.dateTime);
        const formattedTime = timeInLocation.toLocaleTimeString(undefined, {
          hour: 'numeric',
          minute: '2-digit',
        });
        const successMsg = `The current time in ${data.timeZone.replace(/_/g, ' ')} is ${formattedTime}.`;
        logs.push(`getCurrentTime: TimeAPI.io Success for "${timeApiLocation}": ${successMsg}`);
        flush();
        return successMsg;
      }
      throw new Error(`TimeAPI.io returned unexpected data for "${timeApiLocation}". Primary source failed.`);
    } catch (error: any) {
      logs.push(`getCurrentTime: TimeAPI.io Error: ${error?.message || String(error)}`);
      // Fallthrough to WorldTimeAPI
    }

    // Attempt 2: WorldTimeAPI (Fallback Source) with original location
    const worldTimeApiUrlOriginal = `https://worldtimeapi.org/api/timezone/${encodeURIComponent(
      originalLocation
    )}`;
    logs.push(`getCurrentTime: Attempt 2 (WorldTimeAPI original): ${worldTimeApiUrlOriginal}`);

    try {
      const response = await fetch(worldTimeApiUrlOriginal);
      const responseText = await response.text();
      logs.push(
        `getCurrentTime: WorldTimeAPI (original) status: ${response.status}, body: ${responseText.substring(
          0,
          200
        )}`
      );
      if (!response.ok) {
        let errorDetail = `WorldTimeAPI error: Status ${response.status}.`;
        try {
          const errorData = JSON.parse(responseText);
          if (errorData?.error) {
            errorDetail += ` Message: ${errorData.error}`;
            if (String(errorData.error).toLowerCase().includes('unknown location')) {
              errorDetail += ` Location "${originalLocation}" not recognized by WorldTimeAPI.`;
            }
          }
        } catch {
          /* non-JSON body */
        }
        throw new Error(errorDetail);
      }

      const data = JSON.parse(responseText) as { datetime?: string; timezone?: string };
      if (data?.datetime && data?.timezone) {
        const timeInLocation = new Date(data.datetime);
        const formattedTime = timeInLocation.toLocaleTimeString(undefined, {
          hour: 'numeric',
          minute: '2-digit',
        });
        const successMsg = `The current time in ${data.timezone.replace(/_/g, ' ')} is ${formattedTime} (obtained via backup source WorldTimeAPI).`;
        logs.push(`getCurrentTime: WorldTimeAPI Success for "${originalLocation}": ${successMsg}`);
        flush();
        return successMsg;
      }
      throw new Error(`WorldTimeAPI returned unexpected data for "${originalLocation}". Backup source failed.`);
    } catch (error: any) {
      logs.push(`getCurrentTime: WorldTimeAPI (original) Error: ${error?.message || String(error)}`);
    }

    // Attempt 3: Simplified city part if original had comma
    if (originalLocation.includes(',')) {
      const cityPart = originalLocation.split(',')[0].trim();
      if (cityPart && cityPart.toLowerCase() !== originalLocation.toLowerCase()) {
        const worldTimeApiUrlCity = `https://worldtimeapi.org/api/timezone/${encodeURIComponent(cityPart)}`;
        logs.push(`getCurrentTime: Attempt 3 (WorldTimeAPI simplified city "${cityPart}"): ${worldTimeApiUrlCity}`);

        try {
          const response = await fetch(worldTimeApiUrlCity);
          const responseText = await response.text();
          logs.push(
            `getCurrentTime: WorldTimeAPI (simplified city) status: ${response.status}, body: ${responseText.substring(
              0,
              200
            )}`
          );
          if (!response.ok) {
            let errorDetail = `WorldTimeAPI (simplified) error: Status ${response.status}.`;
            try {
              const errorData = JSON.parse(responseText);
              if (errorData?.error) {
                errorDetail += ` Message: ${errorData.error}`;
                if (String(errorData.error).toLowerCase().includes('unknown location')) {
                  errorDetail += ` Location "${cityPart}" not recognized by WorldTimeAPI.`;
                }
              }
            } catch {
              /* non-JSON body */
            }
            throw new Error(errorDetail);
          }

          const data = JSON.parse(responseText) as { datetime?: string; timezone?: string };
          if (data?.datetime && data?.timezone) {
            const timeInLocation = new Date(data.datetime);
            const formattedTime = timeInLocation.toLocaleTimeString(undefined, {
              hour: 'numeric',
              minute: '2-digit',
            });
            const successMsg = `The current time in ${data.timezone.replace(/_/g, ' ')} is ${formattedTime} (obtained using simplified location "${cityPart}" with WorldTimeAPI).`;
            logs.push(`getCurrentTime: WorldTimeAPI Success for simplified city "${cityPart}": ${successMsg}`);
            flush();
            return successMsg;
          }
          throw new Error(
            `WorldTimeAPI returned unexpected data for simplified location "${cityPart}". Simplified city attempt failed.`
          );
        } catch (error: any) {
          logs.push(`getCurrentTime: WorldTimeAPI (simplified city) Error: ${error?.message || String(error)}`);
        }
      }
    }

    // Attempt 4: Remove trailing " City"
    const lowerCaseLocation = originalLocation.toLowerCase();
    if (lowerCaseLocation.endsWith(' city') && lowerCaseLocation.length > ' city'.length) {
      const locationWithoutSuffix = originalLocation.substring(0, originalLocation.length - ' city'.length).trim();
      if (locationWithoutSuffix) {
        const worldTimeApiUrlSuffixRemoved = `https://worldtimeapi.org/api/timezone/${encodeURIComponent(
          locationWithoutSuffix
        )}`;
        logs.push(
          `getCurrentTime: Attempt 4 (WorldTimeAPI suffix-removed "${locationWithoutSuffix}"): ${worldTimeApiUrlSuffixRemoved}`
        );
        try {
          const response = await fetch(worldTimeApiUrlSuffixRemoved);
          const responseText = await response.text();
          logs.push(
            `getCurrentTime: WorldTimeAPI (suffix-removed) status: ${response.status}, body: ${responseText.substring(
              0,
              200
            )}`
          );
          if (!response.ok) {
            let errorDetail = `WorldTimeAPI (suffix-removed) error: Status ${response.status}.`;
            try {
              const errorData = JSON.parse(responseText);
              if (errorData?.error) {
                errorDetail += ` Message: ${errorData.error}`;
                if (String(errorData.error).toLowerCase().includes('unknown location')) {
                  errorDetail += ` Location "${locationWithoutSuffix}" not recognized by WorldTimeAPI.`;
                }
              }
            } catch {
              /* non-JSON body */
            }
            throw new Error(errorDetail);
          }

          const data = JSON.parse(responseText) as { datetime?: string; timezone?: string };
          if (data?.datetime && data?.timezone) {
            const timeInLocation = new Date(data.datetime);
            const formattedTime = timeInLocation.toLocaleTimeString(undefined, {
              hour: 'numeric',
              minute: '2-digit',
            });
            const successMsg = `The current time in ${data.timezone.replace(/_/g, ' ')} is ${formattedTime} (obtained using suffix-removed location "${locationWithoutSuffix}" with WorldTimeAPI).`;
            logs.push(`getCurrentTime: WorldTimeAPI Success for suffix-removed "${locationWithoutSuffix}": ${successMsg}`);
            flush();
            return successMsg;
          }
          throw new Error(
            `WorldTimeAPI returned unexpected data for suffix-removed location "${locationWithoutSuffix}". Suffix-removed attempt failed.`
          );
        } catch (error: any) {
          logs.push(`getCurrentTime: WorldTimeAPI (suffix-removed) Error: ${error?.message || String(error)}`);
        }
      }
    }

    const errorMessage = `I couldn't get the time for "${originalLocation}". All attempts failed. Please check the location name and format or try a nearby major city.`;
    logs.push(`getCurrentTime: All attempts failed for "${originalLocation}".`);
    console.warn(logs.join('\n'));
    return errorMessage;
  } else {
    // No location provided: return server time
    const serverTime = new Date().toLocaleTimeString(undefined, {
      hour: 'numeric',
      minute: '2-digit',
    });
    const msg = `The current time (for me) is ${serverTime}. If you'd like the time for a specific place, tell me the location.`;
    logs.push(`getCurrentTime: No location provided, returning server time: ${msg}`);
    flush();
    return msg;
  }
}

/* -------------------------------- Weather ------------------------------- */

export async function getWeather(
  locationFromPrompt?: string,
  temperatureUnit: TemperatureUnit = 'C',
  service: WeatherServiceOption = 'wttr_in',
  apiKey?: string | null,
  defaultLocationFromSettings?: string | null
): Promise<string> {
  const logs: string[] = [];
  let locationToUse = (locationFromPrompt || defaultLocationFromSettings || '').trim();

  logs.push(
    `getWeather called with: locationFromPrompt="${locationFromPrompt}", temperatureUnit="${temperatureUnit}", service="${service}", defaultLocationFromSettings="${defaultLocationFromSettings}"`
  );
  logs.push(`Effective locationToUse: "${locationToUse}"`);

  if (!locationToUse) {
    logs.push('getWeather: No location specified (neither in prompt nor as default).');
    console.log(logs.join('\n'));
    return "Please specify a location for the weather. For example, try: what's the weather in London?";
  }

  // OpenWeather path
  if (service === 'openweather') {
    if (!apiKey) {
      logs.push("getWeather: 'openweather' selected but no API key provided.");
      console.warn(logs.join('\n'));
      return "Weather service 'openweather' requires an API key.";
    }
    try {
      const geoUrl = `https://api.openweathermap.org/geo/1.0/direct?q=${encodeURIComponent(
        locationToUse
      )}&limit=1&appid=${apiKey}`;
      logs.push(`getWeather: OpenWeatherMap geocode URL: ${geoUrl}`);
      const geoResp = await fetch(geoUrl);
      const geoData = (await geoResp.json()) as Array<{ lat: number; lon: number }>;
      if (!geoResp.ok || !geoData?.[0]) {
        throw new Error(`Unable to find location "${locationToUse}"`);
      }

      const { lat, lon } = geoData[0];
      const units = temperatureUnit === 'F' ? 'imperial' : 'metric';
      const weatherUrl = `https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lon}&units=${units}&appid=${apiKey}`;
      logs.push(`getWeather: OpenWeatherMap weather URL: ${weatherUrl}`);
      const weatherResp = await fetch(weatherUrl);
      const weatherData = await weatherResp.json();
      if (!weatherResp.ok) {
        throw new Error(`HTTP ${weatherResp.status}`);
      }

      const description = weatherData?.weather?.[0]?.description || 'Weather data unavailable';
      const temp = Math.round(weatherData?.main?.temp ?? 0);
      const feelsLike = Math.round(weatherData?.main?.feels_like ?? temp);
      const unitSymbol = temperatureUnit === 'F' ? '°F' : '°C';
      let weatherStr = `Currently in ${locationToUse}: ${description}. The temperature is ${temp}${unitSymbol} (feels like ${feelsLike}${unitSymbol}).`;
      if (weatherData?.main?.humidity != null) {
        weatherStr += ` Humidity is ${weatherData.main.humidity}%.`;
      }
      if (weatherData?.wind?.speed != null) {
        const speed = units === 'imperial' ? `${weatherData.wind.speed} mph` : `${weatherData.wind.speed} m/s`;
        weatherStr += ` Wind speed is ${speed}.`;
      }
      logs.push(`getWeather: Success using OpenWeatherMap: ${weatherStr}`);
      console.log(logs.join('\n'));
      return weatherStr;
    } catch (error: any) {
      logs.push(`getWeather: OpenWeatherMap error: ${error?.message || String(error)}`);
      console.warn(logs.join('\n'));
      return `Sorry, I encountered an error while trying to fetch the weather for "${locationToUse}".`;
    }
  }

  // custom_api concept → fall back to wttr.in
  if (service === 'custom_api') {
    logs.push("getWeather: 'custom_api' selected (concept). Falling back to wttr.in.");
  }

  // wttr.in path
  const wttrUrl = `https://wttr.in/${encodeURIComponent(locationToUse)}?format=j1`;
  logs.push(`getWeather: Attempting to fetch weather from wttr.in: ${wttrUrl}`);
  try {
    const response = await fetch(wttrUrl);
    const responseText = await response.text();
    logs.push(`getWeather: wttr.in response status: ${response.status}, body: ${responseText.substring(0, 300)}`);

    if (!response.ok) {
      let errorInfo = `HTTP error ${response.status}`;
      const lower = responseText.toLowerCase();
      if (lower.includes('unknown location')) {
        errorInfo = `Unknown location "${locationToUse}" according to wttr.in.`;
      } else if (responseText.length > 0 && responseText.length < 100) {
        errorInfo += ` - Server message: ${responseText}`;
      }
      throw new Error(`Failed to fetch weather for "${locationToUse}". ${errorInfo}`);
    }

    const data = JSON.parse(responseText) as any;
    if (data?.current_condition?.[0]) {
      const currentCondition = data.current_condition[0];
      const description: string =
        currentCondition?.weatherDesc?.[0]?.value || 'Not available';
      let temp = parseFloat(currentCondition?.temp_C ?? '0');
      let feelsLike = parseFloat(currentCondition?.FeelsLikeC ?? String(temp));
      let unitSymbol: '°C' | '°F' = '°C';

      if (temperatureUnit === 'F') {
        temp = temp * (9 / 5) + 32;
        feelsLike = feelsLike * (9 / 5) + 32;
        unitSymbol = '°F';
      }

      const tempStr = temp.toFixed(0);
      const feelsLikeStr = feelsLike.toFixed(0);
      const humidity = currentCondition?.humidity;
      const windSpeedKmph = currentCondition?.windspeedKmph;

      let weatherString = `Currently in ${locationToUse}: ${description}. The temperature is ${tempStr}${unitSymbol} (feels like ${feelsLikeStr}${unitSymbol}).`;
      if (humidity != null) {
        weatherString += ` Humidity is ${humidity}%.`;
      }
      if (windSpeedKmph != null) {
        weatherString += ` Wind speed is ${windSpeedKmph} km/h.`;
      }

      logs.push(`getWeather: Success for "${locationToUse}": ${weatherString}`);
      console.log(logs.join('\n'));
      return weatherString;
    }

    // Some edge-patterns indicating invalid/unknown
    if (
      data?.nearest_area?.[0]?.areaName?.[0]?.value?.toLowerCase?.().includes('unknown')
    ) {
      logs.push(`getWeather: Unknown location indicated by nearest_area for "${locationToUse}"`);
      throw new Error(`Sorry, I couldn't find weather data for "${locationToUse}". Please ensure the location is correct.`);
    }
    if (data?.weather?.[0] && data.weather[0].maxtempC === '0' && data.weather[0].mintempC === '0') {
      logs.push(`getWeather: Weather data for "${locationToUse}" seems invalid (temps are 0).`);
      throw new Error(`Sorry, I couldn't find reliable weather data for "${locationToUse}". Please check if the location is correct.`);
    }

    logs.push(`getWeather: Unexpected data structure from wttr.in for location: ${locationToUse}`);
    throw new Error(`Sorry, I received an unexpected response when fetching weather for "${locationToUse}".`);
  } catch (error: any) {
    logs.push(`getWeather: Network or other error: ${error?.message || String(error)}`);
    console.warn(logs.join('\n'));
    const baseErrorMessage =
      (error?.message || '').startsWith("Sorry, I couldn't find") ||
      (error?.message || '').startsWith('Failed to fetch weather')
        ? error.message
        : `Sorry, I encountered an error while trying to fetch the weather for "${locationToUse}". Please check your connection or try again.`;
    return baseErrorMessage;
  }
}

/* --------------------------- Mocked Book Lookup --------------------------- */

export async function mockQueryBookDatabase(bookTitle?: string): Promise<string> {
  if (!bookTitle || bookTitle.trim() === '') {
    return JSON.stringify({
      error: 'Missing book title',
      message: 'I need a book title to look up details. Which book are you interested in?',
    });
  }

  await new Promise((resolve) => setTimeout(resolve, 500));

  const t = bookTitle.toLowerCase();
  if (t.includes('dune')) {
    return JSON.stringify({
      title: bookTitle,
      author: 'Frank Herbert',
      genre: 'Science Fiction',
      summary:
        "Dune is a 1965 science fiction novel by Frank Herbert. It tied with Roger Zelazny's 'This Immortal' for the Hugo Award in 1966 and won the inaugural Nebula Award for Best Novel.",
      publishedYear: 1965,
    });
  } else if (t.includes('gatsby')) {
    return JSON.stringify({
      title: bookTitle,
      author: 'F. Scott Fitzgerald',
      genre: 'Novel',
      summary:
        "The Great Gatsby (1925) follows Nick Carraway's interactions with Jay Gatsby and his obsession to reunite with Daisy Buchanan in the Jazz Age.",
      publishedYear: 1925,
    });
  } else {
    return JSON.stringify({
      error: 'Book not found',
      title: bookTitle,
      message: `Sorry, I couldn't find detailed information for the item titled "${bookTitle}" in the database.`,
    });
  }
}

/* ----------------------------- Mocked Gmail ----------------------------- */

export async function mockCheckGmailUnread(): Promise<string> {
  await new Promise((resolve) => setTimeout(resolve, 700));
  return JSON.stringify({
    unreadCount: 2,
    emails: [
      { from: 'Alice Wonderland', subject: 'Tea Party Invitation', snippet: "You're invited to a mad tea party!" },
      { from: 'Hacker News Digest', subject: 'Top Stories for Today', snippet: 'Check out the latest in tech...' },
    ],
  });
}

export async function mockComposeGmail(input: {
  gmailRecipient?: string;
  gmailSubject?: string;
  gmailBody?: string;
}): Promise<string> {
  await new Promise((resolve) => setTimeout(resolve, 600));
  if (!input.gmailRecipient || !input.gmailSubject || !input.gmailBody) {
    const missing: string[] = [];
    if (!input.gmailRecipient) missing.push('recipient');
    if (!input.gmailSubject) missing.push('subject');
    if (!input.gmailBody) missing.push('body');
    return JSON.stringify({
      error: 'Missing email details',
      message: `I'm missing some details to compose the email. I still need the ${missing.join(', ')}. Could you provide them?`,
    });
  }
  return JSON.stringify({
    success: true,
    message: `Okay, I've "sent" an email to ${input.gmailRecipient} with the subject "${input.gmailSubject}".`,
  });
}

/* ------------------- Legacy wrappers (deprecated paths) ------------------- */

export async function executeKarenPlugin(
  pluginName: string,
  parameters: Record<string, any> = {},
  userId?: string
): Promise<string> {
  console.warn('executeKarenPlugin: This function is deprecated. Use getPluginService().executePlugin() instead.');
  try {
    const { getPluginService } = await import('@/services/pluginService');
    const pluginService = getPluginService();
    const result = await pluginService.executePlugin(pluginName, parameters, { userId });
    return JSON.stringify({
      success: result.success,
      plugin: pluginName,
      result: result.result,
      error: result.error,
      message: result.success
        ? `Successfully executed ${pluginName} plugin.`
        : `Failed to execute ${pluginName} plugin: ${result.error}`,
      timestamp: result.timestamp,
    });
  } catch (error: any) {
    return JSON.stringify({
      success: false,
      plugin: pluginName,
      error: error?.message || 'Unknown error',
      message: `I encountered an error while trying to execute the ${pluginName} plugin.`,
    });
  }
}

export async function queryKarenMemory(
  queryText: string,
  userId?: string,
  sessionId?: string,
  options: {
    topK?: number;
    similarityThreshold?: number;
    tags?: string[];
    timeRange?: [Date, Date];
  } = {}
): Promise<string> {
  console.warn('queryKarenMemory: This function is deprecated. Use getMemoryService().queryMemories() instead.');
  try {
    const { getMemoryService } = await import('@/services/memoryService');
    const memoryService = getMemoryService();
    const memories = await memoryService.queryMemories(queryText, {
      userId,
      sessionId,
      topK: options.topK ?? 5,
      similarityThreshold: options.similarityThreshold ?? 0.7,
      tags: options.tags,
      timeRange: options.timeRange,
    });

    if (memories.length > 0) {
      const formattedMemories = memories.map((mem: any) => ({
        content: mem.content,
        similarity: mem.similarity_score != null ? Number(mem.similarity_score).toFixed(3) : undefined,
        tags: mem.tags,
        timestamp: new Date((mem.timestamp ?? 0) * 1000).toLocaleString(),
      }));
      return JSON.stringify({
        success: true,
        query: queryText,
        found: memories.length,
        memories: formattedMemories,
        message: `Found ${memories.length} relevant memories for your query.`,
      });
    } else {
      return JSON.stringify({
        success: true,
        query: queryText,
        found: 0,
        memories: [],
        message: "I couldn't find any relevant memories for that query.",
      });
    }
  } catch (error: any) {
    return JSON.stringify({
      success: false,
      query: queryText,
      error: error?.message || 'Unknown error',
      message: 'I had trouble searching through my memories right now.',
    });
  }
}

export async function storeKarenMemory(
  content: string,
  userId?: string,
  sessionId?: string,
  options: {
    tags?: string[];
    metadata?: Record<string, any>;
  } = {}
): Promise<string> {
  console.warn('storeKarenMemory: This function is deprecated. Use getMemoryService().storeMemory() instead.');
  try {
    const { getMemoryService } = await import('@/services/memoryService');
    const memoryService = getMemoryService();
    const memoryId = await memoryService.storeMemory(content, {
      tags: options.tags,
      metadata: options.metadata,
      userId,
      sessionId,
    });

    if (memoryId) {
      return JSON.stringify({
        success: true,
        memoryId,
        content: content.substring(0, 100) + (content.length > 100 ? '...' : ''),
        tags: options.tags || [],
        message: "I've stored that information in my memory for future reference.",
      });
    } else {
      return JSON.stringify({
        success: false,
        message: 'I had trouble storing that information in my memory.',
      });
    }
  } catch (error: any) {
    return JSON.stringify({
      success: false,
      error: error?.message || 'Unknown error',
      message: 'I encountered an issue while trying to store that information.',
    });
  }
}

export async function getKarenSystemStatus(): Promise<string> {
  console.warn('getKarenSystemStatus: This function is deprecated. Use getKarenBackend().healthCheck() instead.');
  try {
    const backend = getKarenBackend();
    const [health, metrics] = await Promise.all([backend.healthCheck(), backend.getSystemMetrics()]);
    return JSON.stringify({
      success: true,
      health: {
        status: health.status,
        services: Object.keys(health.services || {}).length,
        timestamp: health.timestamp,
      },
      metrics: {
        cpu_usage: metrics.cpu_usage,
        memory_usage: metrics.memory_usage,
        active_sessions: metrics.active_sessions,
        uptime_hours: metrics.uptime_hours,
        response_time_avg: metrics.response_time_avg,
      },
      message: `System is ${health.status}. CPU: ${metrics.cpu_usage}%, Memory: ${metrics.memory_usage}%, Uptime: ${metrics.uptime_hours}h`,
    });
  } catch (error: any) {
    return JSON.stringify({
      success: false,
      error: error?.message || 'Unknown error',
      message: "I'm having trouble checking my system status right now.",
    });
  }
}

export async function getKarenAnalytics(timeRange: string = '24h'): Promise<string> {
  console.warn('getKarenAnalytics: This function is deprecated. Use getKarenBackend().getUsageAnalytics() instead.');
  try {
    const backend = getKarenBackend();
    const analytics = await backend.getUsageAnalytics(timeRange);
    return JSON.stringify({
      success: true,
      timeRange,
      analytics: {
        total_interactions: analytics.total_interactions,
        unique_users: analytics.unique_users,
        user_satisfaction: analytics.user_satisfaction,
        popular_features: (analytics.popular_features || []).slice(0, 3),
        peak_hours: analytics.peak_hours,
      },
      message: `In the last ${timeRange}: ${analytics.total_interactions} interactions from ${analytics.unique_users} users. Satisfaction: ${analytics.user_satisfaction}/5.0`,
    });
  } catch (error: any) {
    return JSON.stringify({
      success: false,
      timeRange,
      error: error?.message || 'Unknown error',
      message: "I couldn't retrieve analytics data right now.",
    });
  }
}
