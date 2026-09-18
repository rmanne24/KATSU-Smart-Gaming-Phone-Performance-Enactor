package com.katsu.performance;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.webkit.ConsoleMessage;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

public class MainActivity extends Activity {
    private static final String TAG = "KATSU_MAIN";
    private WebView webView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        // Explicitly remove title bar
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        super.onCreate(savedInstanceState);

        // Configure system UI for immersive dark mode
        Window window = getWindow();
        window.addFlags(WindowManager.LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            window.setStatusBarColor(Color.parseColor("#040913"));
            window.setNavigationBarColor(Color.parseColor("#040913"));
        }

        FrameLayout container = new FrameLayout(this);
        container.setBackgroundColor(Color.parseColor("#07101F"));

        webView = new WebView(this);
        webView.setBackgroundColor(Color.parseColor("#07101F"));
        webView.setOverScrollMode(View.OVER_SCROLL_NEVER);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setAllowFileAccessFromFileURLs(true);
        settings.setAllowUniversalAccessFromFileURLs(true);
        settings.setUseWideViewPort(true);
        settings.setLoadWithOverviewMode(true);
        settings.setSupportZoom(false);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        }

        // Bridge native device telemetry to frontend
        webView.addJavascriptInterface(new KatsuBridge(this), "KatsuBridge");

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onConsoleMessage(ConsoleMessage consoleMessage) {
                Log.d(TAG, "[" + consoleMessage.messageLevel() + "] " + consoleMessage.message()
                        + " -- From line " + consoleMessage.lineNumber() + " of " + consoleMessage.sourceId());
                return true;
            }
        });

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                if (url == null) return false;
                if (url.startsWith("file:///android_asset/") || url.startsWith("http://127.0.0.1") || url.startsWith("http://localhost")) {
                    return false;
                }
                try {
                    Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                    startActivity(intent);
                    return true;
                } catch (Exception e) {
                    Log.e(TAG, "Error opening external URL: " + url, e);
                    return false;
                }
            }

            @Override
            public void onReceivedError(WebView view, int errorCode, String description, String failingUrl) {
                Log.e(TAG, "WebView load error: " + errorCode + " (" + description + ") at " + failingUrl);
                // Resilient fallback: stream direct HTML from assets if standard file URL had an issue
                loadHtmlFromAssetStream(view);
            }
        });

        container.addView(webView, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT
        ));

        setContentView(container);

        // Load bundled local assets
        webView.loadUrl("file:///android_asset/www/index.html");
    }

    private void loadHtmlFromAssetStream(WebView view) {
        try {
            InputStream is = null;
            try {
                is = getAssets().open("www/index.html");
            } catch (Exception e1) {
                try {
                    is = getAssets().open("index.html");
                } catch (Exception e2) {
                    Log.e(TAG, "Cannot find index.html in assets", e2);
                    return;
                }
            }

            ByteArrayOutputStream buffer = new ByteArrayOutputStream();
            int nRead;
            byte[] data = new byte[16384];
            while ((nRead = is.read(data, 0, data.length)) != -1) {
                buffer.write(data, 0, nRead);
            }
            buffer.flush();
            byte[] bytes = buffer.toByteArray();
            is.close();

            String html = new String(bytes, StandardCharsets.UTF_8);
            view.loadDataWithBaseURL("file:///android_asset/www/", html, "text/html", "UTF-8", null);
            Log.d(TAG, "Successfully loaded HTML via asset stream fallback.");
        } catch (Exception e) {
            Log.e(TAG, "Failed in loadHtmlFromAssetStream", e);
        }
    }

    @Override
    public void onBackPressed() {
        if (webView != null) {
            webView.evaluateJavascript("typeof handleAndroidBack === 'function' ? handleAndroidBack() : false;", value -> {
                if ("false".equals(value) || value == null) {
                    if (webView.canGoBack()) {
                        webView.goBack();
                    } else {
                        super.onBackPressed();
                    }
                }
            });
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (webView != null) {
            webView.onResume();
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (webView != null) {
            webView.onPause();
        }
    }

    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.destroy();
        }
        super.onDestroy();
    }
}
