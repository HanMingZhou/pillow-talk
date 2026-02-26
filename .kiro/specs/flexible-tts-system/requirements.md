# Requirements Document

## Introduction

This document specifies requirements for a flexible Text-to-Speech (TTS) system for the Pillow Talk backend. The system supports three operational modes: local system TTS (client-side), cloud TTS API (server-side with third-party APIs), and self-hosted TTS (server-side with self-deployed models). The TTS system integrates with the existing chat endpoint and provides standalone TTS conversion capabilities.

## Glossary

- **TTS_System**: The text-to-speech subsystem responsible for converting text to audio
- **TTS_Adapter**: An interface implementation for a specific TTS provider
- **TTS_Provider**: A service that performs text-to-speech conversion (OpenAI, Google Cloud, VITS, etc.)
- **Chat_Endpoint**: The existing `/api/v1/chat` endpoint that returns conversational responses
- **TTS_Endpoint**: The new `/api/v1/tts` endpoint for standalone text-to-speech conversion
- **Audio_Storage**: The subsystem responsible for storing and managing generated audio files
- **TTS_Mode**: The operational mode (local, cloud, or self-hosted)
- **Voice_Profile**: A configuration specifying voice characteristics (voice ID, language, gender)
- **Audio_URL**: A URL pointing to a generated audio file
- **TTS_Request**: A request containing text and TTS configuration parameters
- **Configuration_Manager**: The subsystem that loads and manages TTS provider settings
- **Audio_Cleanup_Service**: The background service that removes expired audio files

## Requirements

### Requirement 1: TTS Provider Selection

**User Story:** As a system administrator, I want to configure which TTS provider the system uses, so that I can choose between local, cloud, or self-hosted options based on my needs.

#### Acceptance Criteria

1. THE Configuration_Manager SHALL load TTS provider settings from the configuration file
2. THE Configuration_Manager SHALL validate that the selected TTS_Mode is one of: local, cloud, or self-hosted
3. WHEN the TTS_Mode is "cloud", THE Configuration_Manager SHALL validate that a cloud provider (openai or google) is specified
4. WHEN the TTS_Mode is "self-hosted", THE Configuration_Manager SHALL validate that a self-hosted provider (vits, bark, xtts, or coqui) is specified
5. IF the configuration is invalid, THEN THE Configuration_Manager SHALL raise a configuration error with a descriptive message

### Requirement 2: TTS Adapter Pattern

**User Story:** As a developer, I want a consistent interface for all TTS providers, so that I can easily add new providers without modifying existing code.

#### Acceptance Criteria

1. THE TTS_System SHALL define a base TTS_Adapter interface with methods: synthesize, get_voices, and validate_config
2. THE TTS_System SHALL implement separate adapter classes for each TTS_Provider
3. WHEN a TTS_Request is received, THE TTS_System SHALL route the request to the appropriate TTS_Adapter based on configuration
4. THE TTS_Adapter SHALL return audio data in a consistent format regardless of the underlying provider
5. IF a TTS_Adapter fails to initialize, THEN THE TTS_System SHALL log the error and raise an initialization exception

### Requirement 3: Local System TTS Mode

**User Story:** As a mobile app user, I want to use my device's built-in TTS, so that I can get speech output without requiring internet connectivity or server resources.

#### Acceptance Criteria

1. WHEN the TTS_Mode is "local", THE Chat_Endpoint SHALL return text responses without generating audio
2. WHEN the TTS_Mode is "local", THE Chat_Endpoint SHALL set the audio_url field to None
3. WHEN the TTS_Mode is "local", THE Chat_Endpoint SHALL include TTS configuration parameters (voice, speed) in the response metadata
4. THE TTS_Endpoint SHALL return an error response with status code 400 when TTS_Mode is "local" and audio generation is requested

### Requirement 4: Cloud TTS API Integration

**User Story:** As a user, I want high-quality cloud-based TTS, so that I can get natural-sounding speech output.

#### Acceptance Criteria

1. WHEN the TTS_Mode is "cloud" and the provider is "openai", THE TTS_System SHALL use the OpenAI TTS API to generate audio
2. WHEN the TTS_Mode is "cloud" and the provider is "google", THE TTS_System SHALL use the Google Cloud Text-to-Speech API to generate audio
3. THE TTS_Adapter SHALL authenticate with the cloud provider using API keys from the configuration
4. WHEN a cloud API request fails, THE TTS_Adapter SHALL retry up to 3 times with exponential backoff
5. IF all retry attempts fail, THEN THE TTS_Adapter SHALL raise a TTS generation error with the provider's error message

### Requirement 5: Self-Hosted TTS Integration

**User Story:** As a system administrator, I want to use self-hosted TTS models, so that I can maintain data privacy and reduce API costs.

#### Acceptance Criteria

1. WHEN the TTS_Mode is "self-hosted", THE TTS_System SHALL connect to the configured TTS service endpoint
2. THE TTS_Adapter SHALL support VITS, Bark, XTTS, and Coqui TTS providers
3. THE TTS_Adapter SHALL send HTTP requests to the self-hosted service with text and voice parameters
4. WHEN the self-hosted service is unreachable, THE TTS_Adapter SHALL raise a connection error within 10 seconds
5. THE TTS_Adapter SHALL parse the audio response from the self-hosted service and return it in the standard format

### Requirement 6: Chat Endpoint Integration

**User Story:** As a mobile app user, I want to receive audio responses along with text in chat conversations, so that I can listen to responses hands-free.

#### Acceptance Criteria

1. WHEN a TTS_Request is received at the Chat_Endpoint with tts_enabled set to true, THE Chat_Endpoint SHALL generate audio for the response text
2. WHEN audio generation succeeds, THE Chat_Endpoint SHALL populate the audio_url field with the Audio_URL
3. WHEN audio generation fails, THE Chat_Endpoint SHALL log the error and return the text response with audio_url set to None
4. THE Chat_Endpoint SHALL pass tts_voice and tts_speed parameters to the TTS_System
5. WHEN tts_enabled is false, THE Chat_Endpoint SHALL skip audio generation and set audio_url to None

### Requirement 7: Standalone TTS Endpoint

**User Story:** As a developer, I want a dedicated TTS endpoint, so that I can convert arbitrary text to speech without going through the chat flow.

#### Acceptance Criteria

1. THE TTS_Endpoint SHALL accept POST requests at `/api/v1/tts` with text, voice, and speed parameters
2. WHEN a valid request is received, THE TTS_Endpoint SHALL generate audio and return the Audio_URL
3. WHEN the TTS_Mode is "local", THE TTS_Endpoint SHALL return an error response with status code 400 and message "TTS is configured for local mode"
4. THE TTS_Endpoint SHALL validate that the text parameter is not empty and does not exceed 5000 characters
5. IF validation fails, THEN THE TTS_Endpoint SHALL return an error response with status code 422 and a descriptive error message

### Requirement 8: Audio Storage and URL Generation

**User Story:** As a system administrator, I want generated audio files to be stored efficiently, so that users can access them via URLs.

#### Acceptance Criteria

1. WHEN audio is generated, THE Audio_Storage SHALL save the audio file with a unique filename
2. THE Audio_Storage SHALL generate a unique filename using a UUID and the appropriate file extension (mp3, wav, or ogg)
3. THE Audio_Storage SHALL return an Audio_URL that clients can use to download the audio file
4. WHERE cloud storage is configured, THE Audio_Storage SHALL upload files to the cloud storage service
5. WHERE local storage is configured, THE Audio_Storage SHALL save files to the configured local directory and generate URLs with the server's base URL

### Requirement 9: Voice Profile Support

**User Story:** As a user, I want to choose from different voices, so that I can personalize the speech output.

#### Acceptance Criteria

1. THE TTS_Adapter SHALL provide a get_voices method that returns available Voice_Profiles for the provider
2. WHEN a TTS_Request specifies a voice parameter, THE TTS_System SHALL use that voice for audio generation
3. WHEN a TTS_Request does not specify a voice parameter, THE TTS_System SHALL use the default voice from configuration
4. IF the requested voice is not available for the provider, THEN THE TTS_System SHALL fall back to the default voice and log a warning
5. THE TTS_System SHALL validate that the voice parameter matches one of the available voices before generation

### Requirement 10: Speech Speed Control

**User Story:** As a user, I want to control the speech speed, so that I can adjust playback to my preference.

#### Acceptance Criteria

1. WHEN a TTS_Request specifies a speed parameter, THE TTS_System SHALL apply that speed to audio generation
2. THE TTS_System SHALL validate that the speed parameter is between 0.25 and 4.0
3. WHEN a TTS_Request does not specify a speed parameter, THE TTS_System SHALL use the default speed of 1.0
4. IF the speed parameter is outside the valid range, THEN THE TTS_System SHALL clamp it to the nearest valid value and log a warning
5. THE TTS_Adapter SHALL convert the speed parameter to the format required by the underlying TTS_Provider

### Requirement 11: Audio File Cleanup

**User Story:** As a system administrator, I want old audio files to be automatically deleted, so that storage space is not exhausted.

#### Acceptance Criteria

1. THE Audio_Cleanup_Service SHALL run periodically to remove expired audio files
2. THE Audio_Cleanup_Service SHALL delete audio files that are older than the configured expiration time (default 24 hours)
3. WHEN an audio file is deleted, THE Audio_Cleanup_Service SHALL log the deletion with the filename and timestamp
4. THE Audio_Cleanup_Service SHALL handle file deletion errors gracefully and continue processing remaining files
5. THE Configuration_Manager SHALL allow administrators to configure the cleanup interval and expiration time

### Requirement 12: Error Handling and Fallback

**User Story:** As a user, I want the system to handle TTS errors gracefully, so that I still receive text responses even when audio generation fails.

#### Acceptance Criteria

1. WHEN audio generation fails at the Chat_Endpoint, THE Chat_Endpoint SHALL return the text response with audio_url set to None
2. WHEN audio generation fails at the TTS_Endpoint, THE TTS_Endpoint SHALL return an error response with status code 500 and the error message
3. THE TTS_System SHALL log all TTS errors with the provider name, error message, and request parameters
4. IF a TTS_Provider is temporarily unavailable, THEN THE TTS_System SHALL raise a service unavailable error
5. THE TTS_System SHALL not retry failed requests at the TTS_Endpoint (client can retry if needed)

### Requirement 13: Audio Format Support

**User Story:** As a developer, I want to support multiple audio formats, so that clients can use the format best suited for their platform.

#### Acceptance Criteria

1. THE TTS_System SHALL support MP3, WAV, and OGG audio formats
2. WHEN a TTS_Request specifies an audio_format parameter, THE TTS_System SHALL generate audio in that format
3. WHEN a TTS_Request does not specify an audio_format parameter, THE TTS_System SHALL use MP3 as the default format
4. IF the requested format is not supported by the TTS_Provider, THEN THE TTS_System SHALL generate audio in the provider's default format and convert it
5. THE Audio_Storage SHALL set the correct Content-Type header when serving audio files

### Requirement 14: Streaming Audio Support

**User Story:** As a user, I want to start hearing audio as soon as possible, so that I don't have to wait for the entire audio file to be generated.

#### Acceptance Criteria

1. WHERE streaming is supported by the TTS_Provider, THE TTS_System SHALL offer a streaming mode
2. WHEN streaming mode is enabled, THE TTS_System SHALL return audio chunks as they are generated
3. THE TTS_Endpoint SHALL support a stream query parameter to enable streaming mode
4. WHEN streaming mode is enabled, THE TTS_Endpoint SHALL return a streaming response with Content-Type "audio/mpeg" or appropriate format
5. IF the TTS_Provider does not support streaming, THEN THE TTS_System SHALL fall back to non-streaming mode and log a warning

### Requirement 15: TTS Configuration Validation

**User Story:** As a system administrator, I want the system to validate TTS configuration at startup, so that I can identify configuration errors early.

#### Acceptance Criteria

1. WHEN the application starts, THE Configuration_Manager SHALL validate all TTS configuration parameters
2. THE Configuration_Manager SHALL verify that required API keys are present for cloud providers
3. THE Configuration_Manager SHALL verify that self-hosted service endpoints are reachable
4. IF configuration validation fails, THEN THE Configuration_Manager SHALL log detailed error messages and prevent application startup
5. THE Configuration_Manager SHALL provide a validate_config method that can be called independently for testing

### Requirement 16: Audio Metadata

**User Story:** As a developer, I want audio files to include metadata, so that clients can display information about the audio.

#### Acceptance Criteria

1. WHEN audio is generated, THE TTS_System SHALL include metadata in the response: duration, format, voice, and speed
2. THE Audio_Storage SHALL store metadata alongside audio files in a JSON sidecar file
3. THE TTS_Endpoint SHALL return metadata in the response body along with the Audio_URL
4. THE Chat_Endpoint SHALL include audio metadata in the response when audio_url is populated
5. THE TTS_System SHALL calculate audio duration from the generated audio file

### Requirement 17: Rate Limiting

**User Story:** As a system administrator, I want to limit TTS requests, so that the system is not overwhelmed by excessive requests.

#### Acceptance Criteria

1. THE TTS_Endpoint SHALL enforce rate limiting based on client IP address
2. THE TTS_System SHALL allow a maximum of 60 requests per minute per IP address
3. WHEN the rate limit is exceeded, THE TTS_Endpoint SHALL return an error response with status code 429
4. THE Configuration_Manager SHALL allow administrators to configure the rate limit threshold
5. THE TTS_System SHALL use a sliding window algorithm for rate limiting

### Requirement 18: TTS Request Logging

**User Story:** As a system administrator, I want to log TTS requests, so that I can monitor usage and troubleshoot issues.

#### Acceptance Criteria

1. WHEN a TTS_Request is received, THE TTS_System SHALL log the request with timestamp, text length, voice, speed, and client IP
2. WHEN audio generation completes, THE TTS_System SHALL log the completion with duration and audio file size
3. WHEN an error occurs, THE TTS_System SHALL log the error with full context including request parameters and error details
4. THE TTS_System SHALL not log the full text content to protect user privacy (only log text length)
5. THE Configuration_Manager SHALL allow administrators to configure the logging level for TTS operations

### Requirement 19: Health Check Endpoint

**User Story:** As a system administrator, I want to monitor TTS system health, so that I can detect and respond to issues proactively.

#### Acceptance Criteria

1. THE TTS_System SHALL provide a health check endpoint at `/api/v1/tts/health`
2. WHEN the health check endpoint is called, THE TTS_System SHALL verify connectivity to the configured TTS_Provider
3. THE health check endpoint SHALL return status code 200 when the TTS_System is healthy
4. THE health check endpoint SHALL return status code 503 when the TTS_Provider is unreachable
5. THE health check endpoint SHALL include provider name, mode, and response time in the response body

### Requirement 20: Text Preprocessing

**User Story:** As a user, I want text to be properly formatted before TTS conversion, so that the audio sounds natural.

#### Acceptance Criteria

1. WHEN text contains URLs, THE TTS_System SHALL replace them with the phrase "link" or remove them based on configuration
2. WHEN text contains markdown formatting, THE TTS_System SHALL strip the formatting characters
3. WHEN text contains code blocks, THE TTS_System SHALL replace them with the phrase "code block" or skip them based on configuration
4. THE TTS_System SHALL normalize whitespace by replacing multiple spaces with a single space
5. THE TTS_System SHALL truncate text that exceeds the maximum length supported by the TTS_Provider and log a warning
