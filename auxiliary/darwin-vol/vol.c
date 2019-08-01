#include <AudioToolbox/AudioServices.h>
#include <CoreAudio/AudioHardware.h>

int main(void)
{
    AudioDeviceID dev = kAudioObjectUnknown;
    Float32 vol = 0.0;
    UInt32 mute = 0;
    UInt32 dev_size, vol_size, mute_size;

    dev_size = sizeof(AudioDeviceID);
    vol_size = sizeof(Float32);
    mute_size = sizeof(UInt32);

    AudioObjectPropertyAddress vol_prop, mute_prop, dev_prop = {
        .mElement = kAudioObjectPropertyElementMaster,
        .mSelector = kAudioHardwarePropertyDefaultOutputDevice,
        .mScope = kAudioObjectPropertyScopeGlobal
    };

    vol_prop = dev_prop;
    vol_prop.mSelector = kAudioHardwareServiceDeviceProperty_VirtualMasterVolume;
    vol_prop.mScope = kAudioDevicePropertyScopeOutput;

    mute_prop = vol_prop;
    mute_prop.mSelector = kAudioDevicePropertyMute;

    if (AudioObjectHasProperty(kAudioObjectSystemObject, &dev_prop))
    {
        AudioObjectGetPropertyData(kAudioObjectSystemObject,
                                   &dev_prop, 0, NULL,
                                   &dev_size, &dev);
    }

    if (dev != kAudioObjectUnknown &&
        AudioObjectHasProperty(dev, &mute_prop) &&
        AudioObjectHasProperty(dev, &vol_prop) &&
        ! AudioObjectGetPropertyData(dev, &mute_prop, 0, NULL, &mute_size, &mute) &&
        ! AudioObjectGetPropertyData(dev, &vol_prop, 0, NULL, &vol_size, &vol))
    {
        vol *= ! mute * 100;
    }

    printf("%f\n", vol);
    return 0;
}
