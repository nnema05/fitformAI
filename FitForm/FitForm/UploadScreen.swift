//
//  UploadScreen.swift
//  FitForm
//
//  Screen 1 of 3.
//  Lets the user pick an inspiration image from their photo library using
//  PhotosPicker. Shows a preview once chosen. "Next" uploads the image to
//  POST /upload-design (APIClient.uploadDesign) and, on success, navigates
//  to FitSelectorScreen carrying both the image and the MLX prediction.
//

import SwiftUI
import PhotosUI

struct UploadScreen: View {

    // MARK: - State

    /// The item selected by PhotosPicker (a reference, not yet decoded).
    @State private var pickerItem: PhotosPickerItem? = nil

    /// The decoded UIImage shown as a preview and carried to the next screen.
    @State private var selectedImage: UIImage? = nil

    /// True while /upload-design is in flight — disables "Next" and shows a spinner.
    @State private var isUploading = false

    /// Set when /upload-design fails; shown as an alert with a dismiss action.
    @State private var uploadError: String? = nil

    /// Set on a successful upload; navigating pushes FitSelectorScreen with this result.
    @State private var uploadResult: UploadDesignResponse? = nil

    // MARK: - Body

    var body: some View {
        VStack(spacing: 24) {

            Spacer()

            // App title / header
            VStack(spacing: 6) {
                Text("FitForm AI")
                    .font(.largeTitle).bold()
                Text("Turn an inspiration image into a garment plan.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            }

            // Image preview or placeholder
            ZStack {
                RoundedRectangle(cornerRadius: 16)
                    .fill(Color(.secondarySystemBackground))
                    .frame(height: 280)

                if let image = selectedImage {
                    Image(uiImage: image)
                        .resizable()
                        .scaledToFill()
                        .frame(height: 280)
                        .clipShape(RoundedRectangle(cornerRadius: 16))
                } else {
                    VStack(spacing: 10) {
                        Image(systemName: "photo.on.rectangle.angled")
                            .font(.system(size: 48))
                            .foregroundStyle(.tertiary)
                        Text("No image selected")
                            .foregroundStyle(.secondary)
                    }
                }
            }
            .padding(.horizontal)

            // PhotosPicker button
            PhotosPicker(
                selection: $pickerItem,
                matching: .images,
                photoLibrary: .shared()
            ) {
                Label("Choose Inspiration Photo", systemImage: "photo.badge.plus")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.bordered)
            .tint(.accentColor)
            .padding(.horizontal)
            // Decode the picked item into a UIImage whenever it changes
            .onChange(of: pickerItem) { _, newItem in
                Task {
                    if let data = try? await newItem?.loadTransferable(type: Data.self),
                       let ui = UIImage(data: data) {
                        selectedImage = ui
                    }
                }
            }

            Spacer()

            // "Next" uploads the image, then navigates once the prediction comes back.
            Button {
                Task { await uploadAndContinue() }
            } label: {
                if isUploading {
                    ProgressView()
                        .frame(maxWidth: .infinity)
                } else {
                    Text("Next")
                        .frame(maxWidth: .infinity)
                }
            }
            .buttonStyle(.borderedProminent)
            .disabled(selectedImage == nil || isUploading)
            .padding(.horizontal)
            .padding(.bottom)
        }
        .navigationTitle("")
        .navigationBarHidden(true)
        .navigationDestination(item: $uploadResult) { result in
            if let image = selectedImage {
                FitSelectorScreen(image: image, uploadResult: result)
            }
        }
        .alert(
            "Upload Failed",
            isPresented: Binding(get: { uploadError != nil }, set: { if !$0 { uploadError = nil } })
        ) {
            Button("OK", role: .cancel) { uploadError = nil }
        } message: {
            Text(uploadError ?? "")
        }
    }

    // MARK: - Networking

    private func uploadAndContinue() async {
        guard let image = selectedImage else { return }
        isUploading = true
        defer { isUploading = false }
        do {
            uploadResult = try await APIClient.uploadDesign(image: image)
        } catch {
            uploadError = (error as? APIError)?.errorDescription ?? error.localizedDescription
        }
    }
}

#Preview {
    NavigationStack {
        UploadScreen()
    }
}
