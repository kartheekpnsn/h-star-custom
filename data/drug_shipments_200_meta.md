| Column Name | Description |
|---|---|
| PATIENT_KEY | Unique anonymized identifier for a patient. Used to calculate unique patient counts and N/R transactions. |
| PATIENT_ST_CD | Two-letter state code representing the patient’s state of residence. |
| PATIENT_TYPE | Indicates whether the shipment is for a New (N) or Refill (R) patient. |
| PRI_ICD_10_CD | Primary ICD-10 diagnosis code associated with the prescription. Used for market and indication analysis. |
| GAP_DAYS | Number of days between expected refill date and actual shipment date (persistence indicator). |
| ADJ_DAYS_SPPL | Adjusted days of supply after accounting for gaps, partial fills, or corrections. |
| RX30_DAYS_SUPPLY | Flag indicating whether the prescription is a standard 30-day supply (1 = yes, 0 = no). |
| SHIP_QTY | Quantity of drug units shipped for the prescription. Often correlates to days of supply. |
| SHIPPED_DT | Date the drug was shipped to the patient. Primary time dimension for shipment trends. |
| LOAD_DT | Date the shipment record was loaded into the system (ETL / ingestion timestamp). |
| TAT | Turnaround time (in days) from prescription initiation to shipment completion. |
| AFFIL_NBR | Affiliation number linking the shipment to a provider group, clinic, or network. |
| SMF_FLAG_ID | Status or fulfillment flag indicating shipment handling state (e.g., standard, manual, exception). |
| HUB_IND_ID | Indicator showing whether the shipment was processed via a patient support hub. |
| HAS_FOUNDATION_GRANT_KW | Flag indicating if a foundation grant was applied to support patient affordability. |
| HAS_COPAY_KW | Flag indicating if a copay assistance program was applied. |
| ASST_OBTAIN_VAL | Dollar value of financial assistance obtained (copay or foundation support). |
| NET_PATIENT_OOP_RANGE_ID | Bucketed range identifier for patient net out-of-pocket cost after assistance. |
| PRI_PATIENT_OOP_RANGE_ID | Bucketed range identifier for patient out-of-pocket cost before assistance. |
| SECURITY_COL | Masked or tokenized security column used to prevent exposure of sensitive identifiers. |
| NDC | National Drug Code identifying the specific drug, strength, and formulation. |
| NDC_DISPLAY | Human-readable display version of the NDC. |
| CODE | Internal drug or product code used for analytics or reporting. |
| MEDISPAN_SHORT_LBL_NM | Short Medi-Span drug label (abbreviated brand/form/strength). |
| MEDISPAN_LBL_NM | Full Medi-Span drug label name. |
| THRPC_CLASS | High-level therapeutic class of the drug (e.g., Oncology, Cardiovascular). |
| TC_SUB_CLASS | Therapeutic subclass used for competitor and market definition logic. |
| MANUFCTR | Manufacturer of the drug product. |
| PBR_KEY | Unique identifier for the prescribing provider. |
| PBR_NPI | National Provider Identifier (NPI) of the prescriber. |
| PBR_NM | Display name of the prescribing provider. |
| PBR_NM_UNQ | Normalized or unique provider name used for deduplication. |
| STATES | Full state name associated with the prescriber location. |
| PLN_KEY | Internal plan identifier linked to the patient’s insurance coverage. |
| PRI_PAYR_KEY | Primary payer identifier for the shipment. |
| PAYR_KEY | Payer key used for payer-level aggregations and filtering. |
| PAYR_NM | Name of the payer (e.g., commercial insurer, government program). |
| PAYR_TYPE | High-level payer category such as Commercial or Government. |