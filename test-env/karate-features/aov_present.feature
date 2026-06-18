Feature: Attestation of Veracity (AoV) presentation
  As a data consumer in a given data exchange
  I want to be able to request the presentation of an Attestation of Veracity (AoV) for the data I receive
  So that I can be assured that veracity requirements have been met

  Background:
    * def apiP = 'http://dva-api-provider:9090'
    * def apiC = 'http://dva-api-consumer:9090'
    * def sleep = function (pause) { java.lang.Thread.sleep(pause * 1000) }

    Given url apiP
    And path 'attestation'
    And request read('../test-data/aov/timestamp_in_range/request-good.json')
    When method post
    Then status 202
    And match response == { id: '#uuid' }

  Scenario: request an AoV presentation
    Given url apiC
    And path 'attestation', 'verify'
    And request read('../test-data/aov/verif-req.json')
    When method post
    Then status 200
    * def id = response.aov.pres_ex_id

    Given url apiC
    And path 'info', 'presentations'
    When method get
    * def matchingLogs = response.filter(log => log.presentationRequestData.pres_ex_id == id)
    Then match matchingLogs == '#[1]'
