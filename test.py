from pyUnfoldedCircleRemote import remote
import asyncio

async def call_api():
    api = remote.Remote('http://192.168.1.186', pin="9447")

    for key in await api.get_api_keys():
        if key.get("name") == api.AUTH_APIKEY_NAME:
            await api.revoke_api_key()

    key = await api.create_api_key()
    await api.get_remote_information()


    # await api.patch_remote_button_settings(auto_brightness=False)
    # await api.patch_remote_display_settings(auto_brightness=False)
    # await api.patch_remote_haptic_settings(haptic_feedback=False)
    # await api.patch_remote_power_saving_settings(display_timeout=10)
    # await api.patch_remote_sound_settings(sound_effects=False)

    await api.patch_remote_button_settings(auto_brightness=True, brightness=65)
    await api.patch_remote_display_settings(auto_brightness=True, brightness=75)
    await api.patch_remote_sound_settings(sound_effects=True, sound_effects_volume=85)
    await api.patch_remote_haptic_settings(haptic_feedback=True)
    await api.patch_remote_power_saving_settings(display_timeout=30, wakeup_sensitivity=2, sleep_timeout=380)

    # await api.patch_remote_button_settings(brightness=55)
    # await api.patch_remote_display_settings(brightness=55)
    # await api.patch_remote_sound_settings(sound_effects_volume=55)
    # #await api.patch_remote_haptic_settings(haptic_feedback=True)
    # await api.patch_remote_power_saving_settings(display_timeout=20, sleep_timeout=280)


if __name__ == "__main__":
    asyncio.run(call_api())