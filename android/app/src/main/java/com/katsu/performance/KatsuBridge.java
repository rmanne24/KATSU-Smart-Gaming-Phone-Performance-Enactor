package com.katsu.performance;

import android.app.ActivityManager;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.BatteryManager;
import android.os.Build;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.webkit.JavascriptInterface;

public class KatsuBridge {
    private final Context context;

    public KatsuBridge(Context context) {
        this.context = context;
    }

    @JavascriptInterface
    public boolean isNative() {
        return true;
    }

    @JavascriptInterface
    public String getDeviceInfo() {
        String model = Build.MODEL;
        String manufacturer = Build.MANUFACTURER;
        String brand = Build.BRAND;
        String hardware = Build.HARDWARE;
        String release = Build.VERSION.RELEASE;
        int sdk = Build.VERSION.SDK_INT;

        return "{"
                + "\"model\":\"" + escape(model) + "\","
                + "\"manufacturer\":\"" + escape(manufacturer) + "\","
                + "\"brand\":\"" + escape(brand) + "\","
                + "\"hardware\":\"" + escape(hardware) + "\","
                + "\"androidVersion\":\"" + escape(release) + "\","
                + "\"sdkInt\":" + sdk
                + "}";
    }

    @JavascriptInterface
    public String getBatteryInfo() {
        try {
            IntentFilter ifilter = new IntentFilter(Intent.ACTION_BATTERY_CHANGED);
            Intent batteryStatus = context.registerReceiver(null, ifilter);

            int level = -1;
            int scale = -1;
            boolean isCharging = false;

            if (batteryStatus != null) {
                level = batteryStatus.getIntExtra(BatteryManager.EXTRA_LEVEL, -1);
                scale = batteryStatus.getIntExtra(BatteryManager.EXTRA_SCALE, -1);
                int status = batteryStatus.getIntExtra(BatteryManager.EXTRA_STATUS, -1);
                isCharging = status == BatteryManager.BATTERY_STATUS_CHARGING ||
                             status == BatteryManager.BATTERY_STATUS_FULL;
            }

            int percent = (level >= 0 && scale > 0) ? Math.round((level / (float) scale) * 100f) : 80;

            return "{\"level\":" + percent + ",\"isCharging\":" + isCharging + "}";
        } catch (Exception e) {
            return "{\"level\":78,\"isCharging\":true}";
        }
    }

    @JavascriptInterface
    public String getMemoryInfo() {
        try {
            ActivityManager activityManager = (ActivityManager) context.getSystemService(Context.ACTIVITY_SERVICE);
            ActivityManager.MemoryInfo memoryInfo = new ActivityManager.MemoryInfo();
            if (activityManager != null) {
                activityManager.getMemoryInfo(memoryInfo);
                double totalGb = memoryInfo.totalMem / (1024.0 * 1024.0 * 1024.0);
                double availGb = memoryInfo.availMem / (1024.0 * 1024.0 * 1024.0);
                double usedGb = totalGb - availGb;
                double usedPercent = (totalGb > 0) ? (usedGb / totalGb) * 100.0 : 47.0;

                return "{"
                        + "\"totalRamGb\":" + String.format(java.util.Locale.US, "%.1f", totalGb) + ","
                        + "\"availRamGb\":" + String.format(java.util.Locale.US, "%.1f", availGb) + ","
                        + "\"usedPercent\":" + String.format(java.util.Locale.US, "%.1f", usedPercent)
                        + "}";
            }
        } catch (Exception ignored) {
        }
        return "{\"totalRamGb\":12.0,\"availRamGb\":6.4,\"usedPercent\":47.0}";
    }

    @JavascriptInterface
    public void vibrate(long milliseconds) {
        try {
            Vibrator v = (Vibrator) context.getSystemService(Context.VIBRATOR_SERVICE);
            if (v != null && v.hasVibrator()) {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    v.vibrate(VibrationEffect.createOneShot(Math.min(milliseconds, 500), VibrationEffect.DEFAULT_AMPLITUDE));
                } else {
                    v.vibrate(Math.min(milliseconds, 500));
                }
            }
        } catch (Exception ignored) {
        }
    }

    private String escape(String s) {
        if (s == null) return "";
        return s.replace("\\", "\\\\").replace("\"", "\\\"");
    }
}
