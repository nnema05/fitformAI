//
//  FitSelectorScreen.swift
//  FitForm
//
//  Screen 2 of 3.
//  Shows the chosen inspiration image, the MLX prediction from
//  /upload-design, and three pickers the user can confirm or override:
//    • Garment type  (Shirt / Dress / Sweater / Pants) — defaults to the prediction
//    • Size          (XS-XXL)
//    • Fit preference (Tight / Regular / Loose / Oversized)
//  Plus an editable primary-material field, pre-filled with a sensible
//  default per garment type. "Generate Plan" navigates to ResultScreen,
//  which fetches the real materials + plan from the backend.
//

import SwiftUI

struct FitSelectorScreen: View {

    // MARK: - Input

    /// The image chosen on UploadScreen, shown as a thumbnail for context.
    let image: UIImage

    /// The MLX classifier's prediction for this image, from POST /upload-design.
    let uploadResult: UploadDesignResponse

    // MARK: - State

    @State private var selection: GarmentSelection
    @State private var primaryMaterial: String

    init(image: UIImage, uploadResult: UploadDesignResponse) {
        self.image = image
        self.uploadResult = uploadResult
        let predictedType = uploadResult.garmentType
        _selection = State(initialValue: GarmentSelection(garmentType: predictedType))
        _primaryMaterial = State(initialValue: predictedType.defaultMaterial)
    }

    // MARK: - Body

    var body: some View {
        ScrollView {
            VStack(spacing: 28) {

                // Thumbnail of the inspiration photo
                Image(uiImage: image)
                    .resizable()
                    .scaledToFill()
                    .frame(height: 220)
                    .clipShape(RoundedRectangle(cornerRadius: 16))
                    .padding(.horizontal)

                // MLX prediction note
                Label(
                    "MLX predicted \(uploadResult.garmentType.displayName) (\(Int(uploadResult.confidence * 100))% confidence). Confirm or change below.",
                    systemImage: "sparkles"
                )
                .font(.caption)
                .foregroundStyle(.secondary)
                .padding(.horizontal)

                // Garment type picker
                VStack(alignment: .leading, spacing: 8) {
                    Text("Garment Type")
                        .font(.headline)
                        .padding(.horizontal)

                    Picker("Garment Type", selection: $selection.garmentType) {
                        ForEach(GarmentType.allCases) { type in
                            Text(type.displayName).tag(type)
                        }
                    }
                    .pickerStyle(.segmented)
                    .padding(.horizontal)
                    // Reset the material field to a sensible default whenever the
                    // garment type changes, since a shirt default ("cotton") rarely
                    // suits a sweater. This does overwrite manual edits on type change —
                    // acceptable for MVP since the field stays editable afterward.
                    .onChange(of: selection.garmentType) { _, newType in
                        primaryMaterial = newType.defaultMaterial
                    }
                }

                // Size picker
                VStack(alignment: .leading, spacing: 8) {
                    Text("Size")
                        .font(.headline)
                        .padding(.horizontal)

                    Picker("Size", selection: $selection.size) {
                        ForEach(Size.allCases) { size in
                            Text(size.rawValue).tag(size)
                        }
                    }
                    .pickerStyle(.segmented)
                    .padding(.horizontal)
                }

                // Fit preference picker
                VStack(alignment: .leading, spacing: 8) {
                    Text("Fit Preference")
                        .font(.headline)
                        .padding(.horizontal)

                    Picker("Fit Preference", selection: $selection.fitPreference) {
                        ForEach(FitPreference.allCases) { fit in
                            Text(fit.displayName).tag(fit)
                        }
                    }
                    .pickerStyle(.segmented)
                    .padding(.horizontal)
                }

                // Primary material — editable, defaults per garment type
                VStack(alignment: .leading, spacing: 8) {
                    Text("Primary Material")
                        .font(.headline)
                        .padding(.horizontal)

                    TextField("e.g. cotton, linen, wool yarn", text: $primaryMaterial)
                        .textFieldStyle(.roundedBorder)
                        .padding(.horizontal)
                }

                // "Generate Plan" navigates to ResultScreen
                NavigationLink {
                    ResultScreen(
                        image: image,
                        selection: selection,
                        primaryMaterial: primaryMaterial,
                        classifierConfidence: uploadResult.confidence
                    )
                } label: {
                    Text("Generate Plan")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .disabled(primaryMaterial.trimmingCharacters(in: .whitespaces).isEmpty)
                .padding(.horizontal)
                .padding(.bottom)
            }
            .padding(.top)
        }
        .navigationTitle("Fit & Type")
        .navigationBarTitleDisplayMode(.inline)
    }
}

#Preview {
    NavigationStack {
        FitSelectorScreen(
            image: UIImage(systemName: "tshirt")!,
            uploadResult: UploadDesignResponse(
                designId: "preview-design",
                garmentType: .shirt,
                confidence: 0.92,
                note: "Preview data"
            )
        )
    }
}
