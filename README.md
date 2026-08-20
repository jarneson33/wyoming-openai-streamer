# Wyoming OpenAI Streamer

[Wyoming protocol](https://github.com/rhasspy/wyoming) server with streaming support for OpenAI-compatible TTS engines.

Ask ChatGPT to tell you a long story, and you will hear the response audio almost immediately instead of waiting for the whole pipeline to finish.

Works with Home Assistant Voice Preview Edition (HAVPE) devices. 

This project builds on [wyoming-piper](https://github.com/rhasspy/wyoming-piper) by Michael Hansen, licensed under MIT.


## Getting started

1. Add the repository and install Wyoming OpenAI Streamer from the Add-on store:

    [![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fjarneson33%2Fwyoming-openai-streamer)

1. Configure Wyoming OpenAI Streamer addon settings:
    1. For OpenAI cloud, set an API key, [get it here](https://platform.openai.com/settings/organization/api-keys)
    2. Optional: set `openai_base_url` to use an OpenAI-compatible local provider instead of the default cloud endpoint (API key can be left empty for local providers)
    3. Optional: set `speaking_rate` as speech speed multiplier (for example `0.8` slower, `1.0` normal, `1.25` faster)
    4. Optional: set `openai_voices` to a comma-separated list (example: `alloy,ash,my_custom_voice`)
    5. Optional: set `openai_languages` to a comma-separated list of locale codes (example: `en-US,fr-FR`)

1. Configure Wyoming Protocol in Home Assistant:
    1. Go to Settings => Integrations => Add Integration => Wyoming Protocol
    2. Add ip/hostname (you can use `127.0.0.1`) and port (the default one is `10200`)

1. Add Wyoming OpenAI Streamer to Voice assistants:
    1. Go to Settings => Voice assistants => choose your assistant => Text-to-speech => Wyoming OpenAI Streamer
    2. Select the desired voice and language, and you are good to go!
