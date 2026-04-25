package com.smallcar.controller.view;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.util.AttributeSet;
import android.view.SurfaceHolder;
import android.view.SurfaceView;

import java.io.BufferedInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;

public class CameraStreamView extends SurfaceView implements SurfaceHolder.Callback {

    private Thread streamThread;
    private volatile boolean running = false;
    private String streamUrl;
    private volatile float targetOffset = 0f;
    private final Paint paint = new Paint();
    private final Paint textPaint = new Paint(Paint.ANTI_ALIAS_FLAG);

    public CameraStreamView(Context context) { super(context); init(); }
    public CameraStreamView(Context context, AttributeSet attrs) { super(context, attrs); init(); }

    private void init() {
        getHolder().addCallback(this);
        textPaint.setColor(Color.WHITE);
        textPaint.setTextSize(32f);
        textPaint.setTextAlign(Paint.Align.CENTER);
    }

    public void startStream(String url) {
        this.streamUrl = url;
        stopStream();
        running = true;
        streamThread = new Thread(this::decodeLoop, "MjpegDecoder");
        streamThread.start();
    }

    public void stopStream() {
        running = false;
        if (streamThread != null) {
            streamThread.interrupt();
            streamThread = null;
        }
    }

    private void decodeLoop() {
        while (running) {
            try {
                HttpURLConnection conn = (HttpURLConnection) new URL(streamUrl).openConnection();
                conn.setConnectTimeout(5000);
                conn.setReadTimeout(10000);
                conn.connect();
                InputStream raw = new BufferedInputStream(conn.getInputStream(), 65536);
                decodeMjpeg(raw);
                conn.disconnect();
            } catch (Exception e) {
                if (!running) break;
                try { Thread.sleep(2000); } catch (InterruptedException ignored) { break; }
            }
        }
    }

    private void decodeMjpeg(InputStream in) throws IOException {
        byte[] buf = new byte[65536];
        int bufLen = 0;

        while (running) {
            int b = in.read();
            if (b == -1) break;

            // Grow buffer
            if (bufLen >= buf.length) {
                byte[] bigger = new byte[buf.length * 2];
                System.arraycopy(buf, 0, bigger, 0, bufLen);
                buf = bigger;
            }
            buf[bufLen++] = (byte) b;

            // Look for JPEG EOI marker 0xFF 0xD9
            if (bufLen >= 2 && buf[bufLen - 2] == (byte) 0xFF && buf[bufLen - 1] == (byte) 0xD9) {
                // Find SOI 0xFF 0xD8
                int soi = -1;
                for (int i = 0; i < bufLen - 1; i++) {
                    if (buf[i] == (byte) 0xFF && buf[i + 1] == (byte) 0xD8) {
                        soi = i;
                        break;
                    }
                }
                if (soi >= 0) {
                    Bitmap bmp = BitmapFactory.decodeByteArray(buf, soi, bufLen - soi);
                    if (bmp != null) drawFrame(bmp);
                }
                bufLen = 0;
            }
        }
    }

    private void drawFrame(Bitmap bmp) {
        updateTargetOffset(bmp);
        SurfaceHolder holder = getHolder();
        Canvas canvas = holder.lockCanvas();
        if (canvas == null) return;
        try {
            canvas.drawBitmap(bmp, null,
                    new android.graphics.Rect(0, 0, getWidth(), getHeight()), paint);
            canvas.drawText(String.format("目标偏移: %.2f", targetOffset), getWidth() / 2f, 48f, textPaint);
        } finally {
            holder.unlockCanvasAndPost(canvas);
            bmp.recycle();
        }
    }

    private void updateTargetOffset(Bitmap bmp) {
        int width = bmp.getWidth();
        int height = bmp.getHeight();
        long totalBrightness = 0;
        long brightWeight = 0;
        long weightedOffset = 0;

        int stepX = Math.max(1, width / 80);
        int stepY = Math.max(1, height / 60);
        int sampleCount = 0;

        for (int y = 0; y < height; y += stepY) {
            for (int x = 0; x < width; x += stepX) {
                int pixel = bmp.getPixel(x, y);
                int r = (pixel >> 16) & 0xFF;
                int g = (pixel >> 8) & 0xFF;
                int b = pixel & 0xFF;
                int brightness = (int) (0.299f * r + 0.587f * g + 0.114f * b);
                totalBrightness += brightness;
                sampleCount++;
            }
        }

        if (sampleCount == 0) {
            targetOffset = 0f;
            return;
        }

        int average = (int) (totalBrightness / sampleCount);
        int threshold = Math.min(255, average + 32);

        for (int y = 0; y < height; y += stepY) {
            for (int x = 0; x < width; x += stepX) {
                int pixel = bmp.getPixel(x, y);
                int r = (pixel >> 16) & 0xFF;
                int g = (pixel >> 8) & 0xFF;
                int b = pixel & 0xFF;
                int brightness = (int) (0.299f * r + 0.587f * g + 0.114f * b);
                if (brightness >= threshold) {
                    int offset = x - width / 2;
                    brightWeight += brightness;
                    weightedOffset += (long) offset * brightness;
                }
            }
        }

        if (brightWeight == 0) {
            targetOffset = 0f;
            return;
        }

        float offsetRatio = (float) weightedOffset / brightWeight / (width / 2f);
        targetOffset = Math.max(-1f, Math.min(1f, offsetRatio));
    }

    public float getTargetOffset() {
        return targetOffset;
    }

    public void drawPlaceholder(String msg) {
        SurfaceHolder holder = getHolder();
        Canvas canvas = holder.lockCanvas();
        if (canvas == null) return;
        try {
            canvas.drawColor(0xFF0A0A0F);
            canvas.drawText(msg, getWidth() / 2f, getHeight() / 2f, textPaint);
        } finally {
            holder.unlockCanvasAndPost(canvas);
        }
    }

    @Override public void surfaceCreated(SurfaceHolder h) {
        drawPlaceholder("摄像头未连接");
    }
    @Override public void surfaceChanged(SurfaceHolder h, int f, int w, int ht) {}
    @Override public void surfaceDestroyed(SurfaceHolder h) { stopStream(); }
}
