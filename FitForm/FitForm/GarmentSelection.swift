//
//  GarmentSelection.swift
//  FitForm
//
//  Enums and a lightweight struct that carries the user's choices
//  (garment type + size + fit preference) through the navigation stack.
//  Raw values are lowercase/uppercase to match the FastAPI backend's wire
//  format exactly (backend/models.py), so no separate mapping table is
//  needed when encoding requests or decoding the MLX prediction.
//  No persistence — values live only for the current session.
//

import Foundation

/// The four garment classes the MLX classifier predicts (backend/models.py GarmentType).
enum GarmentType: String, CaseIterable, Identifiable, Codable {
    case shirt   = "shirt"
    case dress   = "dress"
    case sweater = "sweater"
    case pants   = "pants"

    var id: String { rawValue }

    /// Capitalized label for UI display — rawValue stays lowercase to match the wire format.
    var displayName: String {
        switch self {
        case .shirt:   return "Shirt"
        case .dress:   return "Dress"
        case .sweater: return "Sweater"
        case .pants:   return "Pants"
        }
    }

    /// A sensible starting fabric/yarn per garment type, pre-filled into the
    /// primary-material field on FitSelectorScreen. The user can edit it —
    /// this is just a reasonable default, not a rule the backend enforces.
    var defaultMaterial: String {
        switch self {
        case .shirt:   return "cotton"
        case .dress:   return "linen"
        case .sweater: return "wool yarn"
        case .pants:   return "denim"
        }
    }
}

/// Fit preference the user selects on the Fit Selector screen (backend/models.py FitPreference).
enum FitPreference: String, CaseIterable, Identifiable, Codable {
    case tight     = "tight"
    case regular   = "regular"
    case loose     = "loose"
    case oversized = "oversized"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .tight:     return "Tight"
        case .regular:   return "Regular"
        case .loose:     return "Loose"
        case .oversized: return "Oversized"
        }
    }
}

/// Garment size (backend/models.py Size). Raw values already match the wire
/// format, so they double as the UI label.
enum Size: String, CaseIterable, Identifiable, Codable {
    case xs  = "XS"
    case s   = "S"
    case m   = "M"
    case l   = "L"
    case xl  = "XL"
    case xxl = "XXL"

    var id: String { rawValue }
}

/// Groups the user's selections so they can be passed between screens cleanly.
struct GarmentSelection {
    var garmentType: GarmentType     = .shirt
    var size: Size                   = .m
    var fitPreference: FitPreference = .regular
}
