package com.smallcar.controller.network;

import android.os.Handler;
import android.os.HandlerThread;
import android.os.Looper;

import java.io.IOException;
import java.io.OutputStream;
import java.net.Socket;

public class TcpSocketManager {

    public interface Callback {
        void onConnected();
        void onDisconnected(String reason);
    }

    private HandlerThread thread;
    private Handler handler;
    private final Handler mainHandler = new Handler(Looper.getMainLooper());

    private Socket socket;
    private OutputStream out;
    private Callback callback;

    public void connect(String ip, int port, Callback cb) {
        this.callback = cb;
        if (thread != null) thread.quitSafely();
        thread = new HandlerThread("TcpWorker");
        thread.start();
        handler = new Handler(thread.getLooper());
        handler.post(() -> {
            try {
                socket = new Socket(ip, port);
                socket.setTcpNoDelay(true);
                out = socket.getOutputStream();
                mainHandler.post(() -> cb.onConnected());
            } catch (IOException e) {
                mainHandler.post(() -> cb.onDisconnected(e.getMessage()));
            }
        });
    }

    public void send(String json) {
        if (handler == null || out == null) return;
        handler.post(() -> {
            try {
                out.write(json.getBytes("UTF-8"));
                out.flush();
            } catch (IOException e) {
                mainHandler.post(() -> {
                    if (callback != null) callback.onDisconnected(e.getMessage());
                });
                disconnect();
            }
        });
    }

    public void disconnect() {
        if (handler != null) {
            handler.post(() -> {
                try {
                    if (socket != null) socket.close();
                } catch (IOException ignored) {}
                socket = null;
                out = null;
            });
        }
        if (thread != null) {
            thread.quitSafely();
            thread = null;
        }
        handler = null;
    }

    public boolean isConnected() {
        return socket != null && socket.isConnected() && !socket.isClosed();
    }
}
