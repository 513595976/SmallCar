package com.smallcar.controller.view;

import android.content.Context;
import android.graphics.BlurMaskFilter;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.util.AttributeSet;
import android.view.MotionEvent;
import android.view.View;

public class JoystickView extends View {

    public interface JoystickListener {
        void onMove(float x, float y);
    }

    private final Paint ringPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint glowPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint thumbPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint bgPaint = new Paint(Paint.ANTI_ALIAS_FLAG);

    private float centerX, centerY;
    private float thumbX, thumbY;
    private float maxRadius;
    private float thumbRadius;

    private JoystickListener listener;

    public JoystickView(Context context) { super(context); init(); }
    public JoystickView(Context context, AttributeSet attrs) { super(context, attrs); init(); }

    private void init() {
        // 背景圆环改为完全透明
        bgPaint.setColor(0x00000000);
        bgPaint.setStyle(Paint.Style.FILL);

        glowPaint.setColor(0xFF2979FF);
        glowPaint.setStyle(Paint.Style.STROKE);
        glowPaint.setStrokeWidth(4f);
        glowPaint.setMaskFilter(new BlurMaskFilter(18f, BlurMaskFilter.Blur.OUTER));

        ringPaint.setColor(0xFF2979FF);
        ringPaint.setStyle(Paint.Style.STROKE);
        ringPaint.setStrokeWidth(3f);

        thumbPaint.setColor(0xD9FFFFFF); // 白色，约85%透明度
        thumbPaint.setStyle(Paint.Style.FILL);
        thumbPaint.setMaskFilter(new BlurMaskFilter(8f, BlurMaskFilter.Blur.OUTER));

        setLayerType(LAYER_TYPE_SOFTWARE, null); // required for BlurMaskFilter
    }

    @Override
    protected void onSizeChanged(int w, int h, int oldW, int oldH) {
        centerX = w / 2f;
        centerY = h / 2f;
        thumbX = centerX;
        thumbY = centerY;
        maxRadius = Math.min(w, h) / 2f - 10f;
        thumbRadius = maxRadius * 0.28f;
    }

    @Override
    protected void onDraw(Canvas canvas) {
        // Background circle
        canvas.drawCircle(centerX, centerY, maxRadius, bgPaint);
        // Glow ring
        canvas.drawCircle(centerX, centerY, maxRadius, glowPaint);
        // Solid ring
        canvas.drawCircle(centerX, centerY, maxRadius, ringPaint);
        // Thumb
        canvas.drawCircle(thumbX, thumbY, thumbRadius, thumbPaint);
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
            case MotionEvent.ACTION_MOVE: {
                float dx = event.getX() - centerX;
                float dy = event.getY() - centerY;
                float dist = (float) Math.sqrt(dx * dx + dy * dy);
                if (dist > maxRadius) {
                    dx = dx / dist * maxRadius;
                    dy = dy / dist * maxRadius;
                }
                thumbX = centerX + dx;
                thumbY = centerY + dy;
                invalidate();
                if (listener != null) {
                    listener.onMove(dx / maxRadius, -dy / maxRadius); // y inverted: up = positive
                }
                return true;
            }
            case MotionEvent.ACTION_UP:
            case MotionEvent.ACTION_CANCEL:
                thumbX = centerX;
                thumbY = centerY;
                invalidate();
                if (listener != null) listener.onMove(0f, 0f);
                return true;
        }
        return super.onTouchEvent(event);
    }

    public void setJoystickListener(JoystickListener l) {
        this.listener = l;
    }
}
