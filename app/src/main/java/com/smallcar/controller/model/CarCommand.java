package com.smallcar.controller.model;

public class CarCommand {
    public float x;
    public float y;
    public int speed;
    public int servo;
    public int fire;
    public int behavior;
    public int debug;

    public CarCommand(float x, float y, int speed, int servo, int fire, int behavior, int debug) {
        this.x = clamp(x, -1f, 1f);
        this.y = clamp(y, -1f, 1f);
        this.speed = Math.max(0, Math.min(100, speed));
        this.servo = Math.max(-1, Math.min(1, servo));
        this.fire = Math.max(0, Math.min(1, fire));
        this.behavior = Math.max(0, Math.min(1, behavior));
        this.debug = Math.max(0, Math.min(1, debug));
    }

    public String toJson() {
        return String.format("{\"x\":%.2f,\"y\":%.2f,\"speed\":%d,\"servo\":%d,\"fire\":%d,\"behavior\":%d,\"debug\":%d}\n",
                x, y, speed, servo, fire, behavior, debug);
    }

    private static float clamp(float v, float min, float max) {
        return Math.max(min, Math.min(max, v));
    }
}
