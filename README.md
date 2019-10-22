# openIMIS Backend Policy reference module
This repository holds the files of the openIMIS Backend Policy reference module. It is dedicated to be deployed as a module of [openimis-be_py](https://github.com/openimis/openimis-be_py).

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

## Code climat (develop branch)

[![Maintainability](https://img.shields.io/codeclimate/maintainability/openimis/openimis-be-policy_py.svg)](https://codeclimate.com/github/openimis/openimis-be-policy_py/maintainability)
[![Test Coverage](https://img.shields.io/codeclimate/coverage/openimis/openimis-be-policy_py.svg)](https://codeclimate.com/github/openimis/openimis-be-policy_py)

## ORM mapping:
* tblPolicy > Policy

## Listened Django Signals
None

## Services
* ByInsureeService - WARNING - Today bound to uspPolicyInquiry stored procedure, will be migrated to pyhton code
* EligibilityService - WARNING - Today bound to uspServiceItemEnquiry stored procedure, will be migrated to python code

## Reports (template can be overloaded via report.ReportDefinition)
None

## GraphQL Queries
* policies_by_insuree: gql binding to ByInsureeService
* policy_eligibility_by_insuree: gql binding to EligibilityService, with insuree criteria
* policy_item_eligibility_by_insureegql binding to EligibilityService, with insuree and item  criteria
* policy_service_eligibility_by_insuree: gql binding to EligibilityService, with insuree and service criteria

## GraphQL Mutations - each mutation emits default signals and return standard error lists (cfr. openimis-be-core_py)
None

## Configuration options (can be changed via core.ModuleConfiguration)
* gql_query_policies_by_insuree_perms: required rights to call policies_by_insuree gql
* gql_query_eligibilities_perms: required rights to call policy_eligibility_by_insuree, policy_item_eligibility_by_insureegql, policy_service_eligibility_by_insuree

## openIMIS Modules Dependencies
* claim.models.ClaimOfficer
* insuree.models.Family
* product.models.Product