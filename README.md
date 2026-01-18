# BlueIrisAiProxyServer

A **Smart AI Proxy** for Blue Iris that enhances object detection by combining **Blue Onyx** with **SpeciesNet**.

This service sits between Blue Iris and your existing AI server (Blue Onyx). It acts as a "waterfall" filter:
1.  **Fast Processing**: Images are first sent to **Blue Onyx** for general object detection (people, vehicles, generic animals).
2.  **Specialized Classification**: If a specific trigger object (e.g., "animal") is detected, the image is automatically forwarded to **SpeciesNet** for high-accuracy species identification.
3.  **Unified Result**: The final result (including the specific species name) is returned to Blue Iris as a single response.

## Key Features

*   **Dual-AI Waterfall Logic**: Optimizes performance by only running the heavy SpeciesNet model when necessary.
*   **Drop-in Replacement**: Mimics the **CodeProject.AI API** (`/v1/vision/detection`), so Blue Iris works without plugin changes.
*   **SpeciesNet Integration**: Uses the `speciesnet` v4 PyTorch model for Australian (and other regional) wildlife identification.
*   **Windows Service**: Runs as a robust background service using NSSM.
*   **Configurable**: Easily adjust trigger labels, upstream servers, and regions via environment variables.

## Prerequisites

*   **Windows OS** (10/11 or Server).
*   **Blue Iris** (v5+ recommended).
*   **Blue Onyx**: Running and configured as your primary object detector.
*   **Python 3.10+**: Installed on the system.

## Easiest Installation (Windows Service)

1.  **Clone/Download** this repository to a permanent location (e.g., `C:\BlueIrisAiProxy`).
2.  **Install Dependencies**:
    Open a terminal in the project folder:
    ```powershell
    python -m venv .venv
    .\.venv\Scripts\activate
    pip install -r requirements.txt
    ```
3.  **Configure**:
    *   Rename `.env.example` (if it exists) to `.env`, or create a `.env` file in the root directory.
    *   Edit `.env` to match your setup:
        ```ini
        # URL of your existing Blue Onyx server
        BLUE_ONYX_URL=http://localhost:32168
        
        # Region for SpeciesNet (e.g., AUS, USA, EUR)
        SPECIESNET_REGION=AUS
        
        # Labels that trigger the secondary SpeciesNet check
        TRIGGER_LABELS=["animal", "bird", "cat", "dog"]
        
        # Port for this proxy service
        PORT=8000
        HOST=0.0.0.0
        LOG_LEVEL=INFO
        ```
4.  **Install Service**:
    Open **PowerShell as Administrator** and run:
    ```powershell
    ./scripts/install_service.ps1
    ```
5.  **Start Service**:
    ```powershell
    nssm start BlueIrisAiProxy
    ```

## Blue Iris Configuration

1.  Open **Blue Iris Settings** -> **AI** tab.
2.  Change the **Server URL** to point to this proxy instead of the upstream server directly.
    *   **IP/Host**: `127.0.0.1` (or the IP where this proxy is running).
    *   **Port**: `8000` (or whatever you set in `.env`).
3.  Keep the **Model** settings as usual (they will be passed through to Blue Onyx, though this proxy handles the routing logic).

## Troubleshooting & Logs

*   **Logs**: Check `service.log` in the project directory for detailed activity, errors, and detection results.
*   **Service Status**: Use `nssm status BlueIrisAiProxy` to check if it's running.
*   **Manual Run**: You can stop the service (`nssm stop BlueIrisAiProxy`) and run manually for debugging:
    ```powershell
    .\.venv\Scripts\python.exe server.py
    ```

## Development

*   **Logic**: The core logic is in `src/proxy.py` (`DetectionProxy`).
*   **SpeciesNet**: The wrapper is in `src/inference/speciesnet_wrapper.py`.
*   **Tests**: Run unit tests with `pytest` or `python scripts/test_proxy.py`.

## Verification Results & Debugging Notes

The following findings were documented during the initial deployment and debugging sessions:

### 1. Service Startup & Initialization
- **Status**: Passed.
- **Fix**: Resolved `TypeError` by removing incorrect `geographic_info` argument during SpeciesNet initialization. Service now correctly starts and logs to `service.log`.

### 2. SpeciesNet Geofencing (Wild Turkey)
- **Observation**: "Wild Turkey" was returned as a prediction for Australia (`SPECIESNET_REGION=AUS`).
- **Investigation**: Inspected the underlying SpeciesNet v4 model's geofence map (`geofence_release.20251208.json`).
- **Result**: The model **explicitly allows** Wild Turkey (*Meleagris gallopavo*) in Australia (`"AUS": []`). The service is strictly following the model's rules; this is a data characteristic, not a code bug.

### 3. Bounding Box Scaling
- **Observation**: Coordinates returned were all 0s or small floats.
- **Fix**: Implemented coordinate conversion in `SpeciesNetWrapper`.
    - **Issue**: SpeciesNet returns normalized coordinates (0-1).
    - **Resolution**: Scaled these normalized values by the image dimensions (using PIL) to produce absolute pixel coordinates (`x_min`, `y_min`, `x_max`, `y_max`) as required by Blue Iris.

### 4. GPU Support
- **Status**: Enabled.
- **Dependencies**: Installed PyTorch with CUDA 11.8 support.
- **Verification**: `scripts/check_gpu.py` confirmed `torch.cuda.is_available() == True` and detected the NVIDIA GPU.

### 5. Performance Logging
- **Feature**: Added timing logs to `service.log`.
- **Metrics**: Logs now show:
    - `Blue Onyx inference took X ms` (End-to-End)
    - `SpeciesNet inference took Y ms` (End-to-End)
    - `SpeciesNet internal model.predict took Z ms` (Pure Inference)
