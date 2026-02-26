# Implementation Plan: Flexible TTS System

## Overview

This implementation plan breaks down the Flexible TTS System into manageable coding tasks following the architecture and design patterns specified in the design document. The system will be built using Python with FastAPI, implementing an adapter pattern for TTS providers, with comprehensive error handling, rate limiting, and audio storage management.

The implementation follows five phases: Core Infrastructure, Adapters, API Endpoints, Advanced Features, and Production Readiness. Each task references specific requirements and includes property-based tests to validate correctness properties from the design document.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create Python project with FastAPI, Pydantic, pytest, hypothesis, httpx, and schedule libraries
  - Set up directory structure: src/, tests/unit/, tests/property/, tests/integration/, tests/fixtures/
  - Create requirements.txt with all dependencies
  - Set up pytest configuration with hypothesis settings (min 100 iterations)
  - _Requirements: All_

- [x] 2. Implement configuration management system
  - [x] 2.1 Create configuration data models with Pydantic
    - Implement TTSMode, CloudProvider, SelfHostedProvider enums
    - Implement TTSConfig model with all fields and validators
    - Add validators for mode-specific requirements (cloud_provider, self_hosted_provider)
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  
  - [ ]* 2.2 Write property tests for configuration validation
    - **Property 1: Configuration validation accepts only valid modes**
    - **Validates: Requirements 1.2**
    - **Property 2: Cloud mode requires cloud provider**
    - **Validates: Requirements 1.3**
    - **Property 3: Self-hosted mode requires self-hosted provider**
    - **Validates: Requirements 1.4**
    - **Property 4: Invalid configuration raises descriptive error**
    - **Validates: Requirements 1.5**
  
  - [x] 2.3 Implement ConfigurationManager class
    - Implement _load_config method to load from YAML/JSON
    - Implement validate_config method with startup validation
    - Implement _validate_cloud_config for API key checks
    - Implement _validate_self_hosted_config for endpoint reachability
    - _Requirements: 1.1, 1.5, 15.1, 15.2, 15.3, 15.4_
  
  - [ ]* 2.4 Write property tests for configuration manager
    - **Property 45: Cloud provider requires API keys**
    - **Validates: Requirements 15.2**
    - **Property 46: Self-hosted endpoint is reachable**
    - **Validates: Requirements 15.3**
    - **Property 47: Invalid configuration prevents startup**
    - **Validates: Requirements 15.4**

- [x] 3. Create base TTS adapter interface and data models
  - [x] 3.1 Implement AudioResult and VoiceProfile dataclasses
    - Create AudioResult with audio_data, format, duration, sample_rate, metadata fields
    - Create VoiceProfile with voice_id, name, language, gender, provider_specific fields
    - _Requirements: 2.1, 2.4_
  
  - [x] 3.2 Implement TTSAdapter abstract base class
    - Define abstract methods: synthesize, synthesize_streaming, get_voices, validate_config, health_check
    - Add docstrings with parameter descriptions and exception types
    - _Requirements: 2.1, 2.2_
  
  - [ ]* 3.3 Write property tests for adapter interface
    - **Property 6: All adapters return consistent format**
    - **Validates: Requirements 2.4**
    - **Property 7: Adapter initialization failure raises exception**
    - **Validates: Requirements 2.5**

- [x] 4. Implement text preprocessing service
  - [x] 4.1 Create TextPreprocessor class
    - Implement URL pattern matching and handling (replace/remove/keep)
    - Implement code block pattern matching and handling (replace/skip/keep)
    - Implement markdown stripping (_strip_markdown method)
    - Implement whitespace normalization
    - Implement text truncation with logging
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5_
  
  - [ ]* 4.2 Write property tests for text preprocessing
    - **Property 64: URLs are handled according to configuration**
    - **Validates: Requirements 20.1**
    - **Property 65: Markdown formatting is stripped**
    - **Validates: Requirements 20.2**
    - **Property 66: Code blocks are handled according to configuration**
    - **Validates: Requirements 20.3**
    - **Property 67: Whitespace is normalized**
    - **Validates: Requirements 20.4**
    - **Property 68: Long text is truncated**
    - **Validates: Requirements 20.5**

- [-] 5. Implement audio storage service
  - [x] 5.1 Create AudioStorage class with local storage
    - Implement store_audio method with UUID filename generation
    - Implement metadata sidecar file creation (JSON)
    - Implement URL generation for local storage
    - Implement get_metadata method
    - Implement delete_file method
    - _Requirements: 8.1, 8.2, 8.3, 8.5, 16.2_
  
  - [ ]* 5.2 Write property tests for audio storage
    - **Property 20: Audio filenames are unique**
    - **Validates: Requirements 8.1**
    - **Property 21: Filename format includes UUID and extension**
    - **Validates: Requirements 8.2**
    - **Property 22: Audio URL is accessible**
    - **Validates: Requirements 8.3**
    - **Property 23: Local storage saves to configured directory**
    - **Validates: Requirements 8.5**
    - **Property 49: Metadata is persisted with audio**
    - **Validates: Requirements 16.2**
  
  - [ ] 5.3 Add cloud storage support
    - Implement _upload_to_cloud method for S3/GCS
    - Add cloud URL generation logic
    - _Requirements: 8.4_

- [ ] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Implement local TTS adapter
  - [ ] 7.1 Create LocalAdapter class
    - Implement synthesize method (returns None or raises error)
    - Implement get_voices method (returns empty list or default voice)
    - Implement validate_config method
    - Implement health_check method
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  
  - [ ]* 7.2 Write property tests for local adapter
    - **Property 8: Local mode returns no audio URL**
    - **Validates: Requirements 3.1, 3.2, 3.4**
    - **Property 9: Local mode includes TTS metadata**
    - **Validates: Requirements 3.3**

- [x] 8. Implement OpenAI TTS adapter
  - [x] 8.1 Create OpenAIAdapter class
    - Implement __init__ with OpenAI client initialization
    - Implement synthesize method with OpenAI API calls
    - Implement get_voices method (return supported voices: alloy, echo, fable, onyx, nova, shimmer)
    - Implement retry logic with exponential backoff (max 3 retries)
    - Implement validate_config and health_check methods
    - _Requirements: 4.1, 4.3, 4.4, 4.5_
  
  - [ ]* 8.2 Write property tests for OpenAI adapter
    - **Property 10: Cloud adapter retries on failure**
    - **Validates: Requirements 4.4**
    - **Property 11: Exhausted retries raise error with provider message**
    - **Validates: Requirements 4.5**

- [ ] 9. Implement Google Cloud TTS adapter
  - [ ] 9.1 Create GoogleCloudAdapter class
    - Implement __init__ with Google Cloud client initialization
    - Implement synthesize method with Google Cloud API calls
    - Implement get_voices method
    - Implement retry logic with exponential backoff
    - Implement validate_config and health_check methods
    - Implement _format_to_encoding helper method
    - _Requirements: 4.2, 4.3, 4.4, 4.5_
  
  - [ ]* 9.2 Write property tests for Google Cloud adapter
    - **Property 10: Cloud adapter retries on failure**
    - **Validates: Requirements 4.4**
    - **Property 11: Exhausted retries raise error with provider message**
    - **Validates: Requirements 4.5**

- [ ] 10. Implement self-hosted TTS adapters
  - [ ] 10.1 Create SelfHostedAdapter base class
    - Implement __init__ with httpx client and endpoint configuration
    - Implement synthesize method with HTTP POST to /synthesize endpoint
    - Implement timeout handling (10 seconds)
    - Implement error parsing and exception raising
    - Implement get_voices, validate_config, and health_check methods
    - _Requirements: 5.1, 5.3, 5.4, 5.5_
  
  - [ ] 10.2 Create specific adapters for VITS, Bark, XTTS, Coqui
    - Implement VITSAdapter, BarkAdapter, XTTSAdapter, CoquiAdapter classes
    - Customize request/response formats for each provider
    - _Requirements: 5.2_
  
  - [ ]* 10.3 Write property tests for self-hosted adapters
    - **Property 12: Self-hosted timeout within 10 seconds**
    - **Validates: Requirements 5.4**
    - **Property 13: Self-hosted response parsing returns standard format**
    - **Validates: Requirements 5.5**

- [ ] 11. Implement adapter factory
  - [ ] 11.1 Create AdapterFactory class
    - Implement create_adapter method that routes based on mode and provider
    - Add adapter instantiation logic for all adapter types
    - Add error handling for unsupported providers
    - _Requirements: 2.3_
  
  - [ ]* 11.2 Write property tests for adapter factory
    - **Property 5: Adapter routing matches configuration**
    - **Validates: Requirements 2.3**

- [ ] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Implement TTS system core
  - [x] 13.1 Create TTSSystem class with core orchestration
    - Implement __init__ with dependency injection
    - Implement generate_audio method with preprocessing, validation, and storage
    - Implement _validate_speed method with clamping (0.25-4.0)
    - Implement _validate_voice method with fallback to default
    - Implement health_check method
    - _Requirements: 9.2, 9.3, 9.4, 9.5, 10.1, 10.2, 10.3, 10.4, 16.1, 16.5_
  
  - [ ]* 13.2 Write property tests for TTS system core
    - **Property 24: Specified voice is used**
    - **Validates: Requirements 9.2**
    - **Property 25: Default voice is used when unspecified**
    - **Validates: Requirements 9.3**
    - **Property 26: Invalid voice falls back to default**
    - **Validates: Requirements 9.4, 9.5**
    - **Property 27: Specified speed is applied**
    - **Validates: Requirements 10.1**
    - **Property 28: Speed validation enforces bounds**
    - **Validates: Requirements 10.2**
    - **Property 29: Default speed is used when unspecified**
    - **Validates: Requirements 10.3**
    - **Property 30: Out-of-range speed is clamped**
    - **Validates: Requirements 10.4**
    - **Property 48: Audio metadata includes required fields**
    - **Validates: Requirements 16.1**
    - **Property 52: Audio duration is calculated**
    - **Validates: Requirements 16.5**
  
  - [x] 13.3 Add streaming support to TTSSystem
    - Implement generate_audio_streaming method
    - Add streaming fallback logic
    - _Requirements: 14.1, 14.2, 14.5_
  
  - [ ]* 13.4 Write property tests for streaming
    - **Property 42: Streaming returns incremental chunks**
    - **Validates: Requirements 14.2**
    - **Property 44: Non-streaming fallback when unsupported**
    - **Validates: Requirements 14.5**

- [ ] 14. Implement rate limiting service
  - [ ] 14.1 Create RateLimiter class
    - Implement token bucket algorithm with sliding window
    - Implement check_rate_limit method with thread safety
    - Add configurable rate limit threshold (default 60/minute)
    - _Requirements: 17.1, 17.2, 17.4, 17.5_
  
  - [ ]* 14.2 Write property tests for rate limiter
    - **Property 53: Rate limiting enforced per IP**
    - **Validates: Requirements 17.1**
    - **Property 54: Rate limit threshold is 60 per minute**
    - **Validates: Requirements 17.2**
    - **Property 55: Rate limit exceeded returns 429**
    - **Validates: Requirements 17.3**

- [ ] 15. Implement request and response models
  - [ ] 15.1 Create Pydantic request models
    - Implement ChatRequest with tts_enabled, tts_voice, tts_speed fields
    - Implement TTSRequest with text, voice, speed, audio_format, stream fields
    - Add validators for text length, speed range, audio format
    - _Requirements: 7.4, 7.5, 10.2, 13.1_
  
  - [ ] 15.2 Create Pydantic response models
    - Implement AudioResponse with audio_url, duration, format, voice, speed
    - Implement ChatResponse with message, audio_url, audio_metadata
    - Implement TTSResponse with audio_url and metadata
    - Implement HealthResponse with status, provider, mode, response_time_ms
    - Implement ErrorResponse with error, message, details
    - _Requirements: 16.1, 16.3, 16.4, 19.5_
  
  - [ ]* 15.3 Write property tests for request validation
    - **Property 19: Text validation enforces length limits**
    - **Validates: Requirements 7.4, 7.5**

- [ ] 16. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 17. Implement standalone TTS endpoint
  - [ ] 17.1 Create FastAPI TTS endpoint at /api/v1/tts
    - Implement POST handler with TTSRequest validation
    - Add rate limiting middleware integration
    - Implement local mode check (return 400 error)
    - Implement audio generation with TTSSystem
    - Add error handling with 500 status code
    - Add logging for requests, completions, and errors
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 12.2, 12.3, 12.5, 17.3, 18.1, 18.2, 18.3, 18.4_
  
  - [ ] 17.2 Add streaming support to TTS endpoint
    - Implement streaming response with StreamingResponse
    - Set correct Content-Type header for streaming
    - _Requirements: 14.3, 14.4_
  
  - [ ]* 17.3 Write property tests for TTS endpoint
    - **Property 18: Valid TTS request returns audio URL**
    - **Validates: Requirements 7.2**
    - **Property 34: TTS endpoint failure returns 500 error**
    - **Validates: Requirements 12.2**
    - **Property 37: TTS endpoint does not retry**
    - **Validates: Requirements 12.5**
    - **Property 43: Streaming response has correct Content-Type**
    - **Validates: Requirements 14.4**
    - **Property 50: TTS endpoint returns metadata**
    - **Validates: Requirements 16.3**
    - **Property 56: TTS requests are logged**
    - **Validates: Requirements 18.1**
    - **Property 57: Audio completion is logged**
    - **Validates: Requirements 18.2**
    - **Property 58: Errors are logged with context**
    - **Validates: Requirements 18.3**
    - **Property 59: Full text is not logged**
    - **Validates: Requirements 18.4**

- [ ] 18. Implement chat endpoint integration
  - [ ] 18.1 Integrate TTS into existing chat endpoint
    - Add tts_enabled, tts_voice, tts_speed parameters to ChatRequest
    - Implement conditional audio generation based on tts_enabled
    - Implement graceful degradation (return text on audio failure)
    - Add audio_url and audio_metadata to ChatResponse
    - Pass TTS parameters to TTSSystem
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 12.1, 16.4_
  
  - [ ]* 18.2 Write property tests for chat endpoint TTS integration
    - **Property 14: TTS enabled generates audio**
    - **Validates: Requirements 6.1, 6.2**
    - **Property 15: Audio generation failure returns text gracefully**
    - **Validates: Requirements 6.3, 12.1**
    - **Property 16: TTS parameters are passed through**
    - **Validates: Requirements 6.4**
    - **Property 17: TTS disabled skips audio generation**
    - **Validates: Requirements 6.5**
    - **Property 51: Chat endpoint includes metadata when audio present**
    - **Validates: Requirements 16.4**

- [ ] 19. Implement health check endpoint
  - [ ] 19.1 Create health check endpoint at /api/v1/tts/health
    - Implement GET handler that calls TTSSystem.health_check()
    - Return 200 status when healthy
    - Return 503 status when provider unreachable
    - Include provider name, mode, and response time in response
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5_
  
  - [ ]* 19.2 Write property tests for health check endpoint
    - **Property 60: Health check verifies provider connectivity**
    - **Validates: Requirements 19.2**
    - **Property 61: Healthy system returns 200**
    - **Validates: Requirements 19.3**
    - **Property 62: Unreachable provider returns 503**
    - **Validates: Requirements 19.4**
    - **Property 63: Health check includes provider details**
    - **Validates: Requirements 19.5**

- [ ] 20. Implement audio format support
  - [ ] 20.1 Add format handling to adapters
    - Implement format conversion logic in TTSSystem
    - Add Content-Type header setting in AudioStorage
    - Support MP3, WAV, OGG formats
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_
  
  - [ ]* 20.2 Write property tests for audio format support
    - **Property 38: Specified format is used**
    - **Validates: Requirements 13.2**
    - **Property 39: Default format is MP3**
    - **Validates: Requirements 13.3**
    - **Property 40: Unsupported format is converted**
    - **Validates: Requirements 13.4**
    - **Property 41: Content-Type header matches format**
    - **Validates: Requirements 13.5**

- [ ] 21. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 22. Implement audio cleanup service
  - [x] 22.1 Create AudioCleanupService class
    - Implement start method with schedule setup
    - Implement stop method for graceful shutdown
    - Implement cleanup method that scans and deletes expired files
    - Implement _run_schedule method for background thread
    - Add error handling for individual file deletion failures
    - Add logging for cleanup operations
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_
  
  - [ ]* 22.2 Write property tests for cleanup service
    - **Property 31: Expired files are deleted**
    - **Validates: Requirements 11.2**
    - **Property 32: File deletion is logged**
    - **Validates: Requirements 11.3**
    - **Property 33: Cleanup continues after deletion errors**
    - **Validates: Requirements 11.4**

- [ ] 23. Implement error handling and custom exceptions
  - [ ] 23.1 Create custom exception classes
    - Implement ConfigurationError
    - Implement TTSGenerationError
    - Implement TTSProviderUnavailableError
    - Implement TTSInitializationError
    - Implement RateLimitExceededError
    - _Requirements: 12.1, 12.2, 12.3, 12.4_
  
  - [ ] 23.2 Add error handling to all components
    - Add try-catch blocks with appropriate exception types
    - Implement error logging with context
    - Add error response formatting
    - _Requirements: 12.3, 18.3_
  
  - [ ]* 23.3 Write property tests for error handling
    - **Property 35: TTS errors are logged with context**
    - **Validates: Requirements 12.3**
    - **Property 36: Unavailable provider raises service unavailable error**
    - **Validates: Requirements 12.4**

- [ ] 24. Add comprehensive logging
  - [ ] 24.1 Configure logging system
    - Set up structured logging with appropriate levels
    - Add request logging middleware
    - Implement privacy-preserving logging (text length only, not content)
    - Add configurable logging levels
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_

- [ ] 25. Create configuration file and environment setup
  - [ ] 25.1 Create example configuration files
    - Create config.yaml with all TTS settings
    - Create .env.example with environment variables
    - Document all configuration options
    - _Requirements: 1.1, 11.5, 17.4, 18.5_
  
  - [ ] 25.2 Create application startup and initialization
    - Implement main.py with FastAPI app initialization
    - Add configuration loading and validation at startup
    - Add cleanup service startup
    - Add dependency injection setup
    - _Requirements: 15.1, 15.4_

- [ ] 26. Create audio file serving endpoint
  - [ ] 26.1 Implement GET /audio/{filename} endpoint
    - Serve audio files from local storage
    - Set correct Content-Type headers
    - Add error handling for missing files
    - _Requirements: 8.3, 13.5_

- [ ] 27. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 28. Create integration tests
  - [ ]* 28.1 Write end-to-end integration tests
    - Test chat endpoint with TTS enabled/disabled
    - Test TTS endpoint with all providers (using mocks)
    - Test health check endpoint
    - Test rate limiting across multiple requests
    - Test audio cleanup service
    - Test streaming mode
    - Test error scenarios and graceful degradation

- [ ] 29. Create deployment artifacts
  - [ ] 29.1 Create Dockerfile
    - Set up Python 3.10+ base image
    - Install dependencies
    - Configure audio storage directory
    - Set up entrypoint
    - _Requirements: All_
  
  - [ ] 29.2 Create deployment documentation
    - Document environment variables
    - Document configuration options
    - Document provider setup (API keys, endpoints)
    - Document monitoring and health checks

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation throughout implementation
- Property tests validate universal correctness properties from the design document
- Unit tests (not shown) should be written alongside implementation for specific examples and edge cases
- All adapters should be tested with mock providers to avoid external dependencies during testing
- The implementation uses Python 3.10+ with FastAPI, Pydantic, pytest, and hypothesis
- Configuration validation happens at startup to fail fast on misconfiguration
- Graceful degradation ensures chat endpoint always returns text even if audio fails
- Rate limiting and cleanup services run as background tasks
