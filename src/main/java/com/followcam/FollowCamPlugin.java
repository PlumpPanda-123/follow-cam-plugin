package com.followcam;

import com.google.inject.Provides;
import lombok.extern.slf4j.Slf4j;
import net.runelite.api.Client;
import net.runelite.api.GameState;
import net.runelite.api.Player;
import net.runelite.api.events.ClientTick;
import net.runelite.api.events.GameStateChanged;
import net.runelite.client.config.ConfigManager;
import net.runelite.client.eventbus.Subscribe;
import net.runelite.client.plugins.Plugin;
import net.runelite.client.plugins.PluginDescriptor;

import javax.inject.Inject;

@Slf4j
@PluginDescriptor(
	name = "Follow Cam",
	description = "Camera automatically rotates to face the direction the player is moving, "
		+ "with smooth configurable interpolation.",
	tags = {"camera", "follow", "rotate", "direction", "movement", "smooth"}
)
public class FollowCamPlugin extends Plugin
{
	/**
	 * OSRS uses Jagex Angle Units (JAU): 0–2047 covering 360°.
	 * 0 = south, 512 = west, 1024 = north, 1536 = east.
	 * Both getCameraYaw() and Player.getOrientation() use this system.
	 */
	private static final int ANGLE_MAX = 2048;
	private static final int ANGLE_HALF = ANGLE_MAX / 2;
	private static final double SNAP_THRESHOLD = 0.5;

	@Inject
	private Client client;

	@Inject
	private FollowCamConfig config;

	private boolean initialized = false;
	private double smoothYaw = 0;

	@Override
	protected void startUp()
	{
		initialized = false;
		log.debug("Follow Cam started");
	}

	@Override
	protected void shutDown()
	{
		initialized = false;
		log.debug("Follow Cam stopped");
	}

	@Provides
	FollowCamConfig provideConfig(ConfigManager configManager)
	{
		return configManager.getConfig(FollowCamConfig.class);
	}

	@Subscribe
	public void onGameStateChanged(GameStateChanged event)
	{
		if (event.getGameState() == GameState.LOGGED_IN)
		{
			initialized = false;
		}
	}

	@Subscribe
	public void onClientTick(ClientTick event)
	{
		if (client.getGameState() != GameState.LOGGED_IN)
		{
			return;
		}

		Player local = client.getLocalPlayer();
		if (local == null)
		{
			return;
		}

		if (!initialized)
		{
			// Seed smooth position from the current camera yaw so there is no
			// jarring jump on the first tick after login or enable.
			smoothYaw = client.getCameraYaw();
			initialized = true;
			return;
		}

		double target = local.getOrientation();

		// Find the shortest arc between smoothYaw and target, handling the
		// 0/2048 wrap boundary so we always rotate the "short way round".
		double diff = target - smoothYaw;
		if (diff > ANGLE_HALF)
		{
			diff -= ANGLE_MAX;
		}
		else if (diff < -ANGLE_HALF)
		{
			diff += ANGLE_MAX;
		}

		double factor = config.smoothingSpeed().getFactor();

		if (factor >= 1.0 || Math.abs(diff) < SNAP_THRESHOLD)
		{
			// Snap: either Instant speed or close enough that a sub-pixel step
			// would oscillate forever.
			smoothYaw = target;
		}
		else
		{
			smoothYaw += diff * factor;
			// Normalise to [0, ANGLE_MAX) to keep the value well-behaved.
			smoothYaw = ((smoothYaw % ANGLE_MAX) + ANGLE_MAX) % ANGLE_MAX;
		}

		client.setCameraYawTarget((int) Math.round(smoothYaw));
	}
}
