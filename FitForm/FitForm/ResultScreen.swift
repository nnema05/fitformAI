//
//  ResultScreen.swift
//  FitForm
//
//  Screen 3 of 3.
//  Fetches the real rule-based plan from the backend: POST /estimate-materials
//  and POST /generate-plan run concurrently on appear. Materials and
//  construction steps shown here come straight from planner.py — no
//  duplicated/hardcoded data on the client, so the two can never drift.
//

import SwiftUI

struct ResultScreen: View {

    // MARK: - Input

    let image: UIImage
    let selection: GarmentSelection
    let primaryMaterial: String
    let classifierConfidence: Double

    // MARK: - State

    @State private var materials: EstimateMaterialsResponse? = nil
    @State private var plan: GeneratePlanResponse? = nil
    @State private var errorMessage: String? = nil
    @State private var isLoading = true

    // MARK: - Body

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {

                // Small image reminder at the top
                Image(uiImage: image)
                    .resizable()
                    .scaledToFill()
                    .frame(height: 180)
                    .clipShape(RoundedRectangle(cornerRadius: 16))

                // Garment summary badge
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("\(selection.garmentType.displayName) · \(selection.size.rawValue) · \(selection.fitPreference.displayName) fit")
                            .font(.title2).bold()
                        Label("Rule-based plan from the backend", systemImage: "checkmark.seal")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    Text("~\(Int(classifierConfidence * 100))% conf.")
                        .font(.caption).bold()
                        .padding(.horizontal, 10)
                        .padding(.vertical, 5)
                        .background(Color.accentColor.opacity(0.15))
                        .clipShape(Capsule())
                }

                Divider()

                if isLoading {
                    HStack {
                        Spacer()
                        ProgressView("Generating plan…")
                        Spacer()
                    }
                    .padding(.vertical, 40)
                } else if let errorMessage {
                    VStack(spacing: 12) {
                        Label(errorMessage, systemImage: "exclamationmark.triangle")
                            .font(.callout)
                            .foregroundStyle(.secondary)
                        Button("Retry") {
                            Task { await loadPlan() }
                        }
                        .buttonStyle(.bordered)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 24)
                } else if let materials, let plan {
                    planContent(materials: materials, plan: plan)
                }
            }
            .padding()
        }
        .navigationTitle("Your Garment Plan")
        .navigationBarTitleDisplayMode(.inline)
        .task { await loadPlan() }
    }

    // MARK: - Loaded content

    @ViewBuilder
    private func planContent(materials: EstimateMaterialsResponse, plan: GeneratePlanResponse) -> some View {
        // Materials estimate section
        VStack(alignment: .leading, spacing: 10) {
            Text("Materials Estimate")
                .font(.headline)

            ForEach(materials.materials) { item in
                HStack {
                    Text(item.name)
                    Spacer()
                    Text("\(formatted(item.quantity)) \(item.unit)")
                        .foregroundStyle(.secondary)
                }
                .padding(.vertical, 6)
                .padding(.horizontal, 12)
                .background(Color(.secondarySystemBackground))
                .clipShape(RoundedRectangle(cornerRadius: 8))
            }
        }

        Divider()

        // Pattern pieces (panels)
        VStack(alignment: .leading, spacing: 10) {
            Text("Pattern Pieces")
                .font(.headline)

            Text(plan.panels.joined(separator: " · "))
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }

        Divider()

        // Construction steps section
        VStack(alignment: .leading, spacing: 10) {
            Text("Construction Steps")
                .font(.headline)

            ForEach(plan.steps) { step in
                HStack(alignment: .top, spacing: 12) {
                    Text("\(step.stepNumber)")
                        .font(.caption).bold()
                        .foregroundStyle(.white)
                        .frame(width: 24, height: 24)
                        .background(Color.accentColor)
                        .clipShape(Circle())
                    Text(step.description)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
        }

        // Footer note flagging approximate quantities
        if materials.isApproximate || plan.isApproximate {
            Text("⚠ APPROXIMATE — quantities and steps are rule-based estimates, not measured values. Confirm fit before cutting fabric.")
                .font(.caption)
                .foregroundStyle(.secondary)
                .padding()
                .background(Color(.tertiarySystemBackground))
                .clipShape(RoundedRectangle(cornerRadius: 10))
        }
    }

    /// Trims trailing ".0" for whole-number quantities (e.g. "2" spools, not "2.0" spools).
    private func formatted(_ value: Double) -> String {
        value.truncatingRemainder(dividingBy: 1) == 0
            ? String(Int(value))
            : String(format: "%.2f", value)
    }

    // MARK: - Networking

    private func loadPlan() async {
        isLoading = true
        errorMessage = nil
        do {
            async let materialsRequest = APIClient.estimateMaterials(
                garmentType: selection.garmentType,
                size: selection.size,
                fit: selection.fitPreference
            )
            async let planRequest = APIClient.generatePlan(
                garmentType: selection.garmentType,
                size: selection.size,
                fit: selection.fitPreference,
                primaryMaterial: primaryMaterial
            )
            let (materialsResult, planResult) = try await (materialsRequest, planRequest)
            materials = materialsResult
            plan = planResult
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
        }
        isLoading = false
    }
}

#Preview {
    NavigationStack {
        ResultScreen(
            image: UIImage(systemName: "tshirt")!,
            selection: GarmentSelection(garmentType: .shirt, size: .m, fitPreference: .regular),
            primaryMaterial: "cotton",
            classifierConfidence: 0.92
        )
    }
}
