import sounddevice as sd

print("\n===== DISPOSITIVOS DE ÁUDIO =====\n")

for i, dev in enumerate(sd.query_devices()):
    print(f"{i}: {dev['name']}")

print("\n===============================\n")