package com.smallcar.controller;

import android.app.AlertDialog;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.MotionEvent;
import android.view.WindowManager;
import android.view.View;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import com.smallcar.controller.model.CarCommand;
import com.smallcar.controller.network.TcpSocketManager;
import com.smallcar.controller.view.CameraStreamView;
import com.smallcar.controller.view.JoystickView;

public class MainActivity extends AppCompatActivity {

    private JoystickView joystick;
    private CameraStreamView cameraView;
    private TextView tvIntensity, tvX, tvY;
    private View metricPanel;
    private ImageButton btnServoLeft, btnFire, btnServoRight;
    private ImageButton btnBehaviorToggle;
    private ImageButton btnModeToggle;
    private ImageButton btnSettings;
    private TextView tvModeStatus, tvBehaviorStatus;
    private TextView tvStatus;
    private View statusDot;

    private final TcpSocketManager tcp = new TcpSocketManager();
    private final Handler sendHandler = new Handler(Looper.getMainLooper());

    private float joystickX = 0f, joystickY = 0f;
    private int servoState = 0, fireState = 0, behaviorMode = 0;
    private boolean debugMode = false;
    private boolean sendPending = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        joystick = findViewById(R.id.joystick);
        cameraView = findViewById(R.id.cameraView);
        tvIntensity = findViewById(R.id.tvIntensity);
        tvX = findViewById(R.id.tvX);
        tvY = findViewById(R.id.tvY);
        metricPanel = findViewById(R.id.metricPanel);
        btnBehaviorToggle = findViewById(R.id.btnBehaviorToggle);
        btnModeToggle = findViewById(R.id.btnModeToggle);
        btnServoLeft = findViewById(R.id.btnServoLeft);
        btnFire = findViewById(R.id.btnFire);
        btnServoRight = findViewById(R.id.btnServoRight);
        btnSettings = findViewById(R.id.btnSettings);
        tvModeStatus = findViewById(R.id.tvModeStatus);
        tvBehaviorStatus = findViewById(R.id.tvBehaviorStatus);
        tvStatus = findViewById(R.id.tvStatus);
        statusDot = findViewById(R.id.statusDot);

        btnServoLeft.setAlpha(0.6f);
        btnServoRight.setAlpha(0.6f);
        btnFire.setAlpha(0.6f);

        joystick.setJoystickListener((x, y) -> {
            if (debugMode) {
                // In debug mode, restrict to 4 directions only
                if (Math.abs(x) > Math.abs(y)) {
                    y = 0;
                } else {
                    x = 0;
                }
            }
            joystickX = x;
            joystickY = y;
            float rawIntensity = (float) Math.sqrt(x * x + y * y);
            float intensity = debugMode ? rawIntensity * 0.3f : rawIntensity;
            tvIntensity.setText(String.format("%.2f", intensity));
            tvX.setText(String.format("%.2f", x));
            tvY.setText(String.format("%.2f", y));
            scheduleSend();
        });

        btnServoLeft.setOnTouchListener((v, event) -> {
            if (event.getActionMasked() == MotionEvent.ACTION_DOWN) {
                servoState = -1;
                btnServoLeft.setAlpha(1f);
                scheduleSend();
                return true;
            } else if (event.getActionMasked() == MotionEvent.ACTION_UP
                    || event.getActionMasked() == MotionEvent.ACTION_CANCEL) {
                servoState = 0;
                btnServoLeft.setAlpha(0.6f);
                scheduleSend();
                return true;
            }
            return false;
        });

        btnServoRight.setOnTouchListener((v, event) -> {
            if (event.getActionMasked() == MotionEvent.ACTION_DOWN) {
                servoState = 1;
                btnServoRight.setAlpha(1f);
                scheduleSend();
                return true;
            } else if (event.getActionMasked() == MotionEvent.ACTION_UP
                    || event.getActionMasked() == MotionEvent.ACTION_CANCEL) {
                servoState = 0;
                btnServoRight.setAlpha(0.6f);
                scheduleSend();
                return true;
            }
            return false;
        });

        btnFire.setOnTouchListener((v, event) -> {
            if (event.getActionMasked() == MotionEvent.ACTION_DOWN) {
                fireState = 1;
                btnFire.setAlpha(1f);
                scheduleSend();
                return true;
            } else if (event.getActionMasked() == MotionEvent.ACTION_UP
                    || event.getActionMasked() == MotionEvent.ACTION_CANCEL) {
                fireState = 0;
                btnFire.setAlpha(0.6f);
                scheduleSend();
                return true;
            }
            return false;
        });

        btnBehaviorToggle.setOnClickListener(v -> {
            behaviorMode = 1 - behaviorMode; // Toggle between 0 and 1
            if (behaviorMode == 0) {
                btnBehaviorToggle.setImageResource(R.drawable.ic_wander);
                tvBehaviorStatus.setText("游走");
            } else {
                btnBehaviorToggle.setImageResource(R.drawable.ic_attack);
                tvBehaviorStatus.setText("攻击");
            }
            scheduleSend();
        });

        btnModeToggle.setOnClickListener(v -> {
            debugMode = !debugMode;
            btnModeToggle.setSelected(debugMode);
            tvModeStatus.setText(debugMode ? "调试模式" : "运行模式");
            metricPanel.setVisibility(debugMode ? View.VISIBLE : View.GONE);
            scheduleSend();
        });

        btnSettings.setOnClickListener(v -> showSettingsDialog());

        btnBehaviorToggle.setImageResource(R.drawable.ic_wander);
        btnModeToggle.setSelected(false);
        tvModeStatus.setText("运行模式");
        tvBehaviorStatus.setText("游走");
        metricPanel.setVisibility(View.GONE);
        setStatus(false);
    }

    private void scheduleSend() {
        if (sendPending) return;
        sendPending = true;
        sendHandler.postDelayed(() -> {
            sendPending = false;
            if (tcp.isConnected()) {
                float rawIntensity = (float) Math.sqrt(joystickX * joystickX + joystickY * joystickY);
                float intensity = debugMode ? rawIntensity * 0.3f : rawIntensity;
                int speed = (int) (intensity * 100);
                tvIntensity.setText(String.format("%.2f", intensity));
                CarCommand cmd = new CarCommand(joystickX, joystickY, speed, servoState, fireState, behaviorMode, debugMode ? 1 : 0);
                tcp.send(cmd.toJson());
            }
        }, 50); // ~20Hz
    }

    private void showSettingsDialog() {
        View dialogView = getLayoutInflater().inflate(R.layout.dialog_settings, null);
        EditText etIp = dialogView.findViewById(R.id.etIp);
        EditText etPort = dialogView.findViewById(R.id.etPort);
        EditText etCamera = dialogView.findViewById(R.id.etCamera);

        AlertDialog dialog = new AlertDialog.Builder(this, R.style.HudDialog)
                .setTitle("连接设置")
                .setView(dialogView)
                .setPositiveButton("连接", (d, w) -> {
                    String ip = etIp.getText().toString().trim();
                    String portStr = etPort.getText().toString().trim();
                    String camUrl = etCamera.getText().toString().trim();
                    if (ip.isEmpty() || portStr.isEmpty()) {
                        Toast.makeText(this, "请输入IP和端口", Toast.LENGTH_SHORT).show();
                        return;
                    }
                    int port;
                    try { port = Integer.parseInt(portStr); }
                    catch (NumberFormatException e) { port = 9000; }
                    connectTcp(ip, port);
                    if (!camUrl.isEmpty()) cameraView.startStream(camUrl);
                })
                .setNegativeButton("断开", (d, w) -> {
                    tcp.disconnect();
                    cameraView.stopStream();
                    setStatus(false);
                })
                .show();

        // 设置对话框宽度
        if (dialog.getWindow() != null) {
            WindowManager.LayoutParams layoutParams = new WindowManager.LayoutParams();
            layoutParams.copyFrom(dialog.getWindow().getAttributes());
            layoutParams.width = (int) (getResources().getDisplayMetrics().widthPixels * 0.9); // 屏幕宽度的90%
            dialog.getWindow().setAttributes(layoutParams);
        }
    }

    private void connectTcp(String ip, int port) {
        tvStatus.setText("连接中...");
        statusDot.setBackgroundColor(Color.YELLOW);
        tcp.connect(ip, port, new TcpSocketManager.Callback() {
            @Override public void onConnected() { setStatus(true); }
            @Override public void onDisconnected(String reason) { setStatus(false); }
        });
    }

    private void setStatus(boolean connected) {
        tvStatus.setText(connected ? getString(R.string.status_connected) : getString(R.string.status_disconnected));
        statusDot.setBackgroundColor(connected
                ? getResources().getColor(R.color.status_connected, null)
                : getResources().getColor(R.color.status_disconnected, null));
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        tcp.disconnect();
        cameraView.stopStream();
    }
}
