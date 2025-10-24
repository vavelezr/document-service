# Document Service Microservice

## Overview
The Document Service is a microservice responsible for managing documents within the Carpeta Ciudadana project. It provides functionalities for document creation, retrieval, sharing, and storage, ensuring secure and efficient handling of citizen documents.

## Features
- **Document Management**: Create, retrieve, update, and delete documents.
- **Sharing Capabilities**: Generate share links for documents with configurable access permissions.
- **Storage Integration**: Interact with cloud storage solutions for document storage and retrieval.
- **Thumbnail Generation**: Automatically create thumbnails for document previews.
- **Validation and Security**: Ensure documents meet specified criteria and protect sensitive information.

## Architecture
The Document Service follows a microservices architecture, utilizing various components:
- **Controllers**: Handle incoming requests and responses.
- **Services**: Contain business logic for document operations.
- **Repositories**: Interact with the database for CRUD operations.
- **Middleware**: Implement authentication, validation, and rate limiting.

## Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   ```
2. Navigate to the document service directory:
   ```
   cd document-service
   ```
3. Install dependencies:
   ```
   npm install
   ```

## Usage
To start the Document Service, run:
```
npm start
```
The service will be available at `http://localhost:3000`.

## Testing
Unit tests and integration tests are included in the project. To run tests, use:
```
npm test
```

## API Documentation
Refer to the `docs/api.yml` file for detailed API specifications.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for discussion.

## License
This project is licensed under the MIT License. See the LICENSE file for details.