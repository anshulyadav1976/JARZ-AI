# Integration Tests

End-to-end and integration tests for the full system.

## Test Categories

- **API Integration Tests** - Test backend endpoints
- **Frontend-Backend Integration** - Test full data flow
- **Performance Benchmarks** - Load testing and performance metrics
- **Model Integration** - Test model adapter and predictions

## Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# Integration tests
cd tests
pytest integration/
```
