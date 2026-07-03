Feature: AoV sync verification (JWS drop-in)
  As a data consumer using the JWS drop-in
  I want to synchronously verify a JWS attestation
  So that I can confirm the provider's AoV is authentic

  Background:
    Given url 'http://dva-api-provider:9090'
    * def apiC = 'http://dva-api-consumer:9090'

  Scenario: generate on provider, verify on consumer
    # Step 1: generate AoV on the provider DVA
    Given path 'attestation'
    And request read('../test-data/aov/timestamp_in_range/request-good.json')
    When method post
    Then status 200
    And match response.evaluationPassing == true
    * def jws = response.jws
    * def issuerDidKey = response.issuerDidKey

    # Step 2: verify on the consumer DVA
    Given url apiC
    And path 'attestation', 'verify'
    And request { jws: '#(jws)', attesterDidKey: '#(issuerDidKey)' }
    When method post
    Then status 200
    And match response.verified == true
    And match response.payload == '#object'

  Scenario: tampered JWS is rejected
    Given path 'attestation'
    And request read('../test-data/aov/timestamp_in_range/request-good.json')
    When method post
    Then status 200
    * def jws = response.jws
    * def issuerDidKey = response.issuerDidKey
    * def tampered = jws.substring(0, jws.length() - 4) + 'AAAA'

    Given url apiC
    And path 'attestation', 'verify'
    And request { jws: '#(tampered)', attesterDidKey: '#(issuerDidKey)' }
    When method post
    Then status 200
    And match response.verified == false
