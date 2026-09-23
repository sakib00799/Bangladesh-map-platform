UPDATE test_locations
SET
    name = REPLACE(name, ' Test User', ' Test Donor'),
    type = 'donor'
WHERE type = 'test_user'
  AND name IN (
      'Dhanmondi Test User',
      'Mirpur Test User',
      'Uttara Test User',
      'Narayanganj Test User',
      'Chattogram Test User'
  );

ANALYZE test_locations;
