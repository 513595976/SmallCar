package com.smallcar.controller.model;

public class CarCommand {
    public float x;
    public float y;
    public int speed;
    public int horn;
    public int light;

    public CarCommand(float x, float y, int speed, int horn, int light) {
        this.x = clamp(x, -1f, 1f);
        this.y = clamp(y, -1f, 1f);
        this.speed = Math.max(0, Math.min(100, speed));
        this.horn = horn;
        this.light = light;
    }

    public String toJson() {
        return String.format("{\"x\":%.2f,\"y\":%.2f,\"speed\":%d,\"horn\":%d,\"light\":%d}\n",
                x, y, speed, horn, light);
    }

    private static float clamp(float v, float min, float max) {
        return Math.max(min, Math.min(max, v));
    }
}
