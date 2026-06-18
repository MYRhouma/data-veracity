Feature: Attestation of Veracity (AoV) generation
  As a data provider in a given data exchange
  I want to generate an Attestation of Veracity (AoV) for the data I provide
  So that I can later present it when a consumer requests it

  Background:
    Given url 'http://dva-api-provider:9090'
    * def sleep = function (pause) { java.lang.Thread.sleep(pause * 1000) }
  
  Scenario: create an AoV request with data passing requirements
    Given path 'attestation'
    And request read('../test-data/aov/timestamp_in_range/request-good.json')
    When method post
    Then status 202
    And match response == { id: '#uuid' }
    * def id = response.id

    * sleep(2)

    Given path 'info', 'requests'
    When method get
    * def matchingLogs = response.filter(log => log.requestID == id)
    Then match matchingLogs == '#[1]'
    And match matchingLogs[0].evaluationPassing == true
  
  Scenario: create an AoV request with data failing requirements
    Given path 'attestation'
    And request read('../test-data/aov/timestamp_in_range/request-bad.json')
    When method post
    Then status 202
    And match response == { id: '#uuid' }
    * def id = response.id

    * sleep(2)

    Given path 'info', 'requests'
    When method get
    Then status 200
    * def matchingLogs = response.filter(log => log.requestID == id)
    Then match matchingLogs == '#[1]'
    And match matchingLogs[0].evaluationPassing == false

  Scenario Outline: various quality checks behave correctly
    Given path 'attestation'
    And request read('../test-data/aov/<input>')
    When method post
    Then status 202
    And match response == { id: '#uuid' }
    * def id = response.id

    * sleep(2)

    Given path 'info', 'requests'
    When method get
    Then status 200
    * def matchingLogs = response.filter(log => log.requestID == id)
    Then match matchingLogs == '#[1]'
    And match matchingLogs[0].evaluationPassing == <shouldPass>

    Examples:
      | input                                  | shouldPass |
      | timestamp_in_range/request-good.json   | true       |
      | timestamp_in_range/request-bad.json    | false      |
      # | size_chars/request-good.json           | true       |
      # | size_chars/request-bad.json            | false      |
      # | xapi_field_not_blank/request-good.json | true       |
      # | xapi_field_not_blank/request-bad.json  | false      |
      # | xapi_score_valid/request-good.json     | true       |
      # | xapi_score_valid/request-bad.json      | false      |
      # | xapi_verb_in_set/request-good.json     | true       |
      # | xapi_verb_in_set/request-bad.json      | false      |
