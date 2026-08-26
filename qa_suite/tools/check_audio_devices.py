import sounddevice as sd

def list_devices():
    print("\n--- Verfügbare Audiogeräte ---")
    devices = sd.query_devices()
    for idx, dev in enumerate(devices):
        in_ch = dev['max_input_channels']
        out_ch = dev['max_output_channels']
        rate = dev['default_samplerate']
        print(f"ID {idx:2d}: {dev['name']} | In: {in_ch}, Out: {out_ch} | Default Rate: {rate} Hz")

if __name__ == "__main__":
    list_devices()