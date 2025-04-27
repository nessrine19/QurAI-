# NYUAD Hackathon for Social Good in the Arab World: Focusing on Quantum Computing (QC) and Aritificial Intelligence (AI)
## QurAI معالجُ كَ | Hackathon, April 2025

QURAI delivers a full pipeline from cancer detection to treatment using patient data and quantum optimization to personalize safer, low-toxicity radiotherapy that targets cancer cells and minimize risk over healthy tissue. 

---

## System Workflow

The workflow is organized into four main stages:

### 1. Patient Cell Data Collection
- **Input:** Biological cell parameters from patients.
- **Purpose:** Gather necessary data features (e.g., size, texture, perimeter) for diagnosis.
[Sources of Data](https://www.kaggle.com/datasets/uciml/breast-cancer-wisconsin-data
)
---

### 2. Cancer Diagnosis Classifier (Machine Learning)
- **Input:** Patient cell parameters.
- **Output:** 
  - `1` → Cancer detected (Positive)
  - `0` → No cancer detected (Healthy)
- **Description:** A trained ML model classifies whether the input data suggests the presence of cancer.

---

### 3. Quantum Optimization for Beam Angle Selection
- **Trigger:** Executed **only if cancer is detected**.
- **Process:**
  - Formulate the beam angle selection problem as a **QUBO** (Quadratic Unconstrained Binary Optimization) problem.
  - Solve using **Quantum Approximate Optimization Algorithm (QAOA)**.
  - Perform classical post-processing to refine and validate the results.
- **Purpose:** Find the optimal radiation beam angles for therapy, minimizing damage to healthy tissues while maximizing impact on the tumor.

---

### 4. Recommended Treatment Plan
- **Output:** Personalized, optimized treatment plan based on quantum-classical hybrid computation results.
- **Goal:** Offer an effective and precise treatment recommendation to improve patient outcomes.

---

## Technologies Used

- **Machine Learning:** Cancer classification based on patient cell data.
- **Quantum Computing:** QUBO formulation and QAOA for optimization tasks.
- **Classical Computing:** Post-processing optimization results.
- **Medical Data Processing:** Handling and interpreting biological parameters.

---

## Future Enhancements
- Expand dataset to include multiple cancer types.
- Integrate more quantum algorithms for other treatment parameters.
- Improve classical-quantum hybrid processing pipeline.
- Add explainability modules for ML predictions to increase trust and transparency.

---

## 🌍 Impact
Supports UN SDGs:  
- **Good Health and Well-being (3)**  
- **Industry, Innovation, and Infrastructure (9)**  
- **Sustainable Cities and Communities (11)**


Presentation link : https://www.canva.com/design/DAGlt6_FInQ/UdR-tRDGpVxuW7hIIK8q5w
