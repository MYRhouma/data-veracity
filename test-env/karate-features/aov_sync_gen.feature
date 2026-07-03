Feature: AoV sync generation (JWS drop-in)
  As a data provider using the JWS drop-in (DVA_ATTESTATION_MODE=sync)
  I want to synchronously generate an Attestation of Veracity (AoV)
  So that I receive a signed JWS in the same HTTP response

  Background:
    Given url 'http://dva-api-provider:9090'

  Scenario: sync AoV with passing data returns 200 + JWS
    Given path 'attestation'
    And request read('../test-data/aov/timestamp_in_range/request-good.json')
    When method post
    Then status 200
    And match response == { requestId: '#uuid', issuerDidKey: '#string', jws: '#string', vcId: '#string', evaluationPassing: true, evaluationResults: '#array', vcIssuedDate: '#string' }

  Scenario: sync AoV with failing data returns 200 + no JWS
    Given path 'attestation'
    And request read('../test-data/aov/timestamp_in_range/request-bad.json')
    When method post
    Then status 200
    And match response.evaluationPassing == false
    * assert !response.jws
