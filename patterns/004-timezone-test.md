# Timezone-dependent test failure

## Symptom

A date or time test passes locally and fails in CI, often near midnight.

## Mechanism

Test data or application code uses a naive datetime or the host timezone, so
the same instant maps to different dates on different machines.

## Observable signature

- failures cluster around UTC midnight or daylight-saving transitions;
- the assertion compares dates derived in different timezones;
- datetime literals have no explicit timezone;
- rerunning under `TZ=UTC` changes the result.

## Generic defense

Pin fixtures to explicit timezones and stable instants. Run the relevant suite
under UTC as part of validation and test daylight-saving boundaries directly.

## Fixture TODO

Add one Madrid/UTC boundary example and one daylight-saving transition.
