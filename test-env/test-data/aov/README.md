# Validation Guide

This document provides examples of valid and invalid statements, along with explanations of why certain statements are invalid.

## ✅ Valid Schema Statement

```json
{
  "statement": {
    "actor": {
      "account": {
        "name": "3f324ffd4112ed63",
        "homePage": "https://www.inokufu.com/"
      },
      "objectType": "Agent"
    },
    "verb": {
      "id": "https://w3id.org/xapi/netc/verbs/accessed",
      "display": {
        "en": "accessed"
      }
    },
    "object": {
      "objectType": "Activity",
      "id": "https://www.inokufu.com/",
      "definition": {
        "type": "https://w3id.org/xapi/acrossx/activities/webpage",
        "name": {
          "en": "Inokufu | Better data for better learning"
        },
        "extensions": {
          "https://w3id.org/xapi/acrossx/extensions/type": "course"
        }
      }
    },
    "context": {
      "contextActivities": {
        "category": [
          {
            "id": "https://w3id.org/xapi/lms",
            "definition": {
              "type": "http://adlnet.gov/expapi/activities/profile"
            },
            "objectType": "Activity"
          }
        ]
      },
      "extensions": {
        "http://id.tincanapi.com/extension/duration": "0s",
        "http://id.tincanapi.com/extension/browser-info": "Firefox 129.0"
      }
    },
    "version": "1.0.0",
    "timestamp": "2024-09-04T17:01:06.887Z",
    "id": "c68c9086-fdfe-405e-aeac-fc5fa6e6bcc9",
    "authority": {
      "objectType": "Agent",
      "account": {
        "name": "Mockup WALRUC write",
        "homePage": "https://www.inokufu.com/"
      }
    }
  }
}
```

## ❌ Invalid Schema Statement

```json
{
  "statement": {
    "actor": {
      "account": {
        "name": "3f324ffd4112ed63",
        "homePage": "https://invalidurl.com/"
      }
    },
    "verb": {
      "id": "https://incorrect-url.com/verbs/accessed",
      "display": {
        "en": "accessed"
      }
    },
    "object": {
      "objectType": "Activity",
      "id": "https://www.inokufu.com/",
      "definition": {
        "type": "https://w3id.org/xapi/acrossx/activities/webpage",
        "name": {
          "en": "Inokufu | Better data for better learning"
        },
        "extensions": {
          "https://w3id.org/xapi/acrossx/extensions/type": "course"
        }
      }
    },
    "context": {
      "contextActivities": {
        "category": [
          {
            "id": "https://w3id.org/xapi/lms",
            "definition": {
              "type": "http://adlnet.gov/expapi/activities/profile"
            },
            "objectType": "Activity"
          }
        ]
      },
      "extensions": {
        "http://id.tincanapi.com/extension/duration": "0s",
        "http://id.tincanapi.com/extension/browser-info": "Firefox 129.0"
      }
    },
    "version": "1.0.0",
    "timestamp": "2024-09-04T17:01:06.887Z",
    "id": "c68c9086-fdfe-405e-aeac-fc5fa6e6bcc9",
    "authority": {
      "objectType": "Agent",
      "account": {
        "name": "Mockup WALRUC write",
        "homePage": "https://www.inokufu.com/"
      }
    },
    "wrongField": "This should cause an error"
  }
}
```

### Why is this invalid?

1. Missing required field: `objectType` is missing in the `actor` field *(schema compliance issue)*
2. Incorrect field (`wrongField`) *(schema compliance issue)*
3. Invalid verb URL: The `id` for the verb has been changed to `"https://incorrect-url.com/verbs/accessed"` *(profile compliance issue)*
4. Invalid actor URL: The `homePage` URL in the actor section has been changed to `"https://invalidurl.com/"`  *(profile compliance issue)*


## ✅ Valid actor score (actor score within experience range min/max)

```json
{
  "statement": {
    "authority": {
      "objectType": "Agent",
      "name": "Mockup LOMCT write",
      "mbox": "mailto:contact@inokufu.com"
    },
    "timestamp": "2024-04-11T14:17:43.686Z",
    "version": "1.0.0",
    "context": {
      "extensions": {
        "http://schema&46;prometheus-x&46;org/extension/username": "victorhugo",
        "http://schema&46;prometheus-x&46;org/extension/biography": "history teacher at high school"
      },
      "language": "en"
    },
    "actor": {
      "name": "victorhugo",
      "mbox": "mailto:lauriane.marxer+lomct1@inokufu.com",
      "objectType": "Agent"
    },
    "verb": {
      "id": "http://id.tincanapi.com/verb/reviewed"
    },
    "object": {
      "id": "https://en.wikipedia.org/wiki/Nonformal_learning",
      "objectType": "Activity"
    },
    "result": {
      "score": {
        "scaled": 1,
        "raw": 3,
        "min": 0,
        "max": 5
      },
      "response": "This is a good article on informal learning. I recommend it."
    },
    "id": "ee689a9b-1007-4425-9f75-a678f575797d",
    "stored": "2024-09-06T12:49:53.935Z"
  }
}
```

## ❌ Invalid actor score statement

```json
{
  "statement": {
    "authority": {
      "objectType": "Agent",
      "name": "Mockup LOMCT write",
      "mbox": "mailto:contact@inokufu.com"
    },
    "timestamp": "2024-04-11T14:17:43.686Z",
    "version": "1.0.0",
    "context": {
      "extensions": {
        "http://schema&46;prometheus-x&46;org/extension/username": "victorhugo",
        "http://schema&46;prometheus-x&46;org/extension/biography": "history teacher at high school"
      },
      "language": "en"
    },
    "actor": {
      "name": "victorhugo",
      "mbox": "mailto:lauriane.marxer+lomct1@inokufu.com",
      "objectType": "Agent"
    },
    "verb": {
      "id": "http://id.tincanapi.com/verb/reviewed"
    },
    "object": {
      "id": "https://en.wikipedia.org/wiki/Nonformal_learning",
      "objectType": "Activity"
    },
    "result": {
      "score": {
        "scaled": 1.4,
        "raw": 7,
        "min": 0,
        "max": 5
      },
      "response": "This is a good article on informal learning. I recommend it."
    },
    "id": "ee689a9b-1007-4425-9f75-a678f575797d",
    "stored": "2024-09-06T12:49:53.935Z"
  }
}
```

### Why is this invalid?

1. The scale is higher than 1.
2. The raw score exceeds the allowed range – it is higher than the maximum.
