# Use Cases for Akita Meshtastic IPFS Plugin

This document lists practical scenarios where the Akita Meshtastic IPFS Plugin is useful.

- Sensor Data Collection: Devices publish periodic sensor readings (temperature, humidity, GPS) to the gateway which stores them on IPFS. Devices and web apps can retrieve historic readings via CIDs.
- File Distribution: Small configuration files, maps, or imagery can be distributed to nodes via IPFS CIDs broadcast over Meshtastic.
- Offline Content Sync: Nodes can cache previously fetched IPFS content for offline access and re-share CIDs across the mesh.
- Emergency Messaging: Broadcast emergency messages with accompanying data (e.g., images, coordinates) stored on IPFS and referenced by CID for later retrieval.
- Secure Sharing: Use the gateway's pre-shared key mechanism to restrict which devices can store/retrieve content via the gateway.
- Low-bandwidth Firmware/Config Updates: Distribute small firmware patches or configuration bundles via IPFS CIDs and apply updates on devices that request them.

Notes:
- Keep payloads small (CID references rather than large binary blobs) to fit Meshtastic message size limits.
- Monitor device resources when enabling caching and local storage.
