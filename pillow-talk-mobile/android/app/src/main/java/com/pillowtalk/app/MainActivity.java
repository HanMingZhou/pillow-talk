package com.pillowtalk.app;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

public class MainActivity extends BridgeActivity {
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        // 启动 Python 后端服务器
        startPythonBackend();
    }
    
    private void startPythonBackend() {
        if (!Python.isStarted()) {
            Python.start(new AndroidPlatform(this));
        }
        
        Python py = Python.getInstance();
        
        // 在后台线程启动服务器
        new Thread(() -> {
            try {
                py.getModule("simple_server").callAttr("main");
            } catch (Exception e) {
                e.printStackTrace();
            }
        }).start();
    }
}
