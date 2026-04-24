package com.smallcar.controller;

import android.app.AlertDialog;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.SeekBar;
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
    private SeekBar speedBar;
    private Button btnHorn, btnLight, btnSettings;
    private TextView tvStatus;
    private View statusDot;

    private final TcpSocketManager tcp = new TcpSocketManager();
    private final Handler sendHandler = new Handler(Looper.getMainLooper());

    private float joystickX = 0f, joystickY = 0f;
    private int hornState = 0, lightState = 0;
    private boolean sendPending = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        joystick = findViewById(R.id.joystick);
        cameraView = findViewById(R.id.cameraView);
        speedBar = findViewById(R.id.speedBar);
        btnHorn = findViewById(R.id.btnHorn);
        btnLight = findViewById(R.id.btnLight);
        btnSettings = findViewById(R.id.btnSettings);
        tvStatus = findViewById(R.id.tvStatus);
        statusDot = findViewById(R.id.statusDot);

        joystick.setJoystickListener((x, y) -> {
            joystickX = x;
            joystickY = y;
            scheduleSend();
        });

        btnHorn.setOnClickListener(v -> {
            hornState = hornState == 0 ? 1 : 0;
            btnHorn.setAlpha(hornState == 1 ? 1f : 0.6f);
            scheduleSend();
        });

        btnLight.setOnClickListener(v -> {
            lightState = lightState == 0 ? 1 : 0;
            btnLight.setAlpha(lightState == 1 ? 1f : 0.6f);
            scheduleSend();
        });

        btnSettings.setOnClickListener(v -> showSettingsDialog());

        setStatus(false);
    }

    private void scheduleSend() {
        if (sendPending) return;
        sendPending = true;
        sendHandler.postDelayed(() -> {
            sendPending = false;
            if (tcp.isConnected()) {
                int speed = speedBar.getProgress();
                CarCommand cmd = new CarCommand(joystickX, joystickY, speed, hornState, lightState);
                tcp.send(cmd.toJson());
            }
        }, 50); // ~20Hz
    }

    private void showSettingsDialog() {
        View dialogView = getLayoutInflater().inflate(R.layout.dialog_settings, null);
        EditText etIp = dialogView.findViewById(R.id.etIp);
        EditText etPort = dialogView.findViewById(R.id.etPort);
        EditText etCamera = dialogView.findViewById(R.id.etCamera);

        new AlertDialog.Builder(this, R.style.HudDialog)
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
