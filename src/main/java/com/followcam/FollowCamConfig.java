package com.followcam;

import net.runelite.client.config.Config;
import net.runelite.client.config.ConfigGroup;
import net.runelite.client.config.ConfigItem;

@ConfigGroup("followcam")
public interface FollowCamConfig extends Config
{
	enum SmoothingSpeed
	{
		INSTANT("Instant", 1.0),
		FAST("Fast", 0.20),
		MEDIUM("Medium", 0.10),
		SLOW("Slow", 0.05);

		private final String label;
		private final double factor;

		SmoothingSpeed(String label, double factor)
		{
			this.label = label;
			this.factor = factor;
		}

		public double getFactor()
		{
			return factor;
		}

		@Override
		public String toString()
		{
			return label;
		}
	}

	@ConfigItem(
		keyName = "smoothingSpeed",
		name = "Smoothing Speed",
		description = "How quickly the camera rotates to match the player's facing direction. "
			+ "Instant snaps immediately; Slow gives a cinematic sweep.",
		position = 0
	)
	default SmoothingSpeed smoothingSpeed()
	{
		return SmoothingSpeed.MEDIUM;
	}
}
