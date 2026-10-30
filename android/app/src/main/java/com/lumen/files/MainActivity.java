package com.lumen.files;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.webkit.ValueCallback;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

/**
 * Lumen Files — the whole UI lives in assets/index.html.
 * This shell only provides a full-window WebView, persistent storage
 * (localStorage -> app data dir) and a native back key that is handed
 * to the web layer first.
 */
public class MainActivity extends Activity {

    private static final String START_URL = "file:///android_asset/index.html";
    private static final int REQ_STORAGE = 1001;
    private WebView web;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);

        web = new WebView(this);
        web.setBackgroundColor(Color.parseColor("#0b1030"));
        web.setOverScrollMode(View.OVER_SCROLL_NEVER);
        web.setVerticalScrollBarEnabled(false);
        web.setHorizontalScrollBarEnabled(false);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);          // localStorage: keeps the file tree between launches
        s.setDatabaseEnabled(true);
        s.setAllowFileAccess(true);
        s.setAllowContentAccess(true);
        s.setMediaPlaybackRequiresUserGesture(false);   // tap sounds
        s.setSupportZoom(false);
        s.setBuiltInZoomControls(false);
        s.setDisplayZoomControls(false);
        s.setTextZoom(100);
        s.setCacheMode(WebSettings.LOAD_NO_CACHE);

        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) {
                return true;   // everything stays inside the app
            }
        });

        if (state != null) {
            web.restoreState(state);
        } else {
            web.loadUrl(START_URL);
        }
        setContentView(web);

        askForStorage();
    }

    /** The one permission this app declares: storage. Asked once, never nagged. */
    private void askForStorage() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.M || Build.VERSION.SDK_INT > 32) {
            return;   // 30+ is covered by the "All files access" toggle, 33+ has no runtime dialog
        }
        if (checkSelfPermission(Manifest.permission.READ_EXTERNAL_STORAGE)
                == PackageManager.PERMISSION_GRANTED) {
            return;
        }
        String[] wanted = Build.VERSION.SDK_INT <= Build.VERSION_CODES.P
                ? new String[]{Manifest.permission.READ_EXTERNAL_STORAGE,
                               Manifest.permission.WRITE_EXTERNAL_STORAGE}
                : new String[]{Manifest.permission.READ_EXTERNAL_STORAGE};
        requestPermissions(wanted, REQ_STORAGE);
    }

    @Override
    public void onRequestPermissionsResult(int code, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(code, permissions, results);
        // granted or not, the UI is unaffected - nothing here blocks the app
    }

    @Override
    public void onBackPressed() {
        if (web == null) {
            super.onBackPressed();
            return;
        }
        web.evaluateJavascript(
                "(function(){try{return (window.lumenBack && window.lumenBack())?'1':'0'}catch(e){return '0'}})()",
                new ValueCallback<String>() {
                    @Override
                    public void onReceiveValue(String value) {
                        if (!"\"1\"".equals(value)) {
                            finish();   // nothing left to close -> leave the app
                        }
                    }
                });
    }

    @Override
    protected void onSaveInstanceState(Bundle out) {
        super.onSaveInstanceState(out);
        if (web != null) web.saveState(out);
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (web != null) web.onPause();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (web != null) web.onResume();
    }

    @Override
    protected void onDestroy() {
        if (web != null) {
            web.setWebViewClient(null);
            web.destroy();
            web = null;
        }
        super.onDestroy();
    }
}
