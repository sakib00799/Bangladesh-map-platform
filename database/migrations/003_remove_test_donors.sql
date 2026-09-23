DELETE FROM test_locations
WHERE type = 'donor'
  AND name IN (
      'Dhanmondi Test Donor',
      'Mirpur Test Donor',
      'Uttara Test Donor',
      'Narayanganj Test Donor',
      'Chattogram Test Donor'
  );

ANALYZE test_locations;
