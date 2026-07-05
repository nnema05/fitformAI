//
//  APIModels.swift
//  FitForm
//
//  Codable mirrors of the FastAPI response/request schemas in
//  backend/models.py. Property names are camelCase; APIClient's
//  JSONEncoder/JSONDecoder use .convertToSnakeCase / .convertFromSnakeCase
//  so these map to the backend's snake_case JSON automatically.
//

import Foundation

// MARK: - /upload-design

struct UploadDesignResponse: Codable, Identifiable, Hashable {
    var id: String { designId }
    let designId: String
    let garmentType: GarmentType
    let confidence: Double
    let note: String
}

// MARK: - /estimate-materials

struct MaterialItem: Codable, Identifiable {
    var id: String { name + unit }
    let name: String
    let quantity: Double
    let unit: String
}

struct EstimateMaterialsResponse: Codable {
    let garmentType: GarmentType
    let size: Size
    let fitPreference: FitPreference
    let materials: [MaterialItem]
    let isApproximate: Bool
}

// MARK: - /generate-plan

struct ConstructionStep: Codable, Identifiable {
    var id: Int { stepNumber }
    let stepNumber: Int
    let description: String
}

struct GeneratePlanResponse: Codable {
    let garmentType: GarmentType
    let size: Size
    let fitPreference: FitPreference
    let primaryMaterial: String
    let panels: [String]
    let steps: [ConstructionStep]
    let isApproximate: Bool
}

// MARK: - Error envelope

/// FastAPI's default error body shape: `{"detail": "..."}`.
struct APIErrorDetail: Decodable {
    let detail: String
}
