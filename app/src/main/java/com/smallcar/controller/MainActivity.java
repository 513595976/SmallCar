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

    private static final int BEHAVIOR_WANDER = 0;
    private static final int BEHAVIOR_ATTACK = 1;

    private float joystickX = 0f;
    private float joystickY = 0f;
    private float joystickIntensity = 0f;
    private int servoState = 0, fireState = 0, behaviorMode = BEHAVIOR_WANDER;
    private boolean debugMode = false;
    private boolean sendPending = false;
    private boolean wanderModeJustSwitched = false;

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
            joystickIntensity = Math.min(1f, (float) Math.sqrt(x * x + y * y));
            updateJoystickMetrics();
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
            behaviorMode = 1 - behaviorMode; // Toggle between wander and attack
            updateBehaviorMode();
            scheduleSend();
        });

        btnModeToggle.setOnClickListener(v -> {
            debugMode = !debugMode;
            btnModeToggle.setSelected(debugMode);
            btnModeToggle.setImageResource(debugMode ? R.drawable.ic_debug : R.drawable.ic_run);
            tvModeStatus.setText(debugMode ? "调试模式" : "运行模式");
            metricPanel.setVisibility(debugMode ? View.VISIBLE : View.GONE);
            scheduleSend();
        });

        btnSettings.setOnClickListener(v -> showSettingsDialog());

        updateBehaviorMode();
        btnModeToggle.setSelected(false);
        tvModeStatus.setText("运行模式");
        metricPanel.setVisibility(View.GONE);
        setStatus(false);
    }

    private void scheduleSend() {
        if (sendPending) return;
        sendPending = true;
        sendHandler.postDelayed(() -> {
            sendPending = false;
            if (tcp.isConnected()) {
                float commandIntensity = debugMode ? joystickIntensity * 0.3f : joystickIntensity;
                int speed = (int) (commandIntensity * 100);
                int servo = computeServoCommand();
                updateJoystickMetrics();
                CarCommand cmd = new CarCommand(joystickX, joystickY, speed, servo, fireState, behaviorMode, debugMode ? 1 : 0);
                tcp.send(cmd.toJson());
            }
        }, 50); // ~20Hz
    }

    private void updateJoystickMetrics() {
        tvIntensity.setText(String.format("%.2f", joystickIntensity));
        tvX.setText(String.format("%.2f", joystickX));
        tvY.setText(String.format("%.2f", joystickY));
    }

    private void updateBehaviorMode() {
        if (behaviorMode == BEHAVIOR_WANDER) {
            btnBehaviorToggle.setImageResource(R.drawable.ic_wander);
            tvBehaviorStatus.setText("游走");
            btnServoLeft.setEnabled(true);
            btnServoRight.setEnabled(true);
            btnServoLeft.setAlpha(1.0f);
            btnServoRight.setAlpha(1.0f);
            wanderModeJustSwitched = true; // 标记刚刚切换到游走模式
        } else {
            btnBehaviorToggle.setImageResource(R.drawable.ic_attack);
            tvBehaviorStatus.setText("攻击");
            btnServoLeft.setEnabled(false);
            btnServoRight.setEnabled(false);
            btnServoLeft.setAlpha(0.3f);
            btnServoRight.setAlpha(0.3f);
            wanderModeJustSwitched = false;
        }
    }

    private int computeServoCommand() {
        if (behaviorMode == BEHAVIOR_WANDER) {
            if (wanderModeJustSwitched) {
                wanderModeJustSwitched = false; // 清除标志，下次允许手动控制
                return 0; // 切换时调整到90度
            }
            return servoState; // 释放后允许手动控制
        } else if (behaviorMode == BEHAVIOR_ATTACK) {
            return calculateAttackServo();
        }
        return servoState;
    }

    private int calculateAttackServo() {
        float targetOffset = getCameraTargetOffset();
        if (targetOffset < -0.2f) {
            return -1;
        } else if (targetOffset > 0.2f) {
            return 1;
        }
        return 0;
    }

    private float getCameraTargetOffset() {
        if (cameraView != null) {
            return cameraView.getTargetOffset();
        }
        return 0f;
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
            layoutParams.width = (int) (getResources().getDisplayMetrics().widthPixels * 0.45); // 约为屏幕宽度的一半
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
