//
//  APIClient.swift
//  FitForm
//
//  Thin networking layer over the FastAPI backend (backend/main.py).
//  One function per route; all are async/throws so screens can `await` them
//  directly inside a `.task { }` or a button's Task { }.
//
//  Local dev only, per CLAUDE.md — no auth, no cloud, points at localhost.
//  If running on a physical device (not the Simulator), replace baseURL's
//  host with your Mac's LAN IP, since "localhost" on a device means the
//  device itself, not your Mac.
//

import Foundation
import UIKit

enum APIError: LocalizedError {
    case invalidResponse
    case server(String)
    case decoding(Error)
    case network(Error)

    var errorDescription: String? {
        switch self {
        case .invalidResponse:
            return "The server sent back something unexpected."
        case .server(let message):
            return message
        case .decoding:
            return "Couldn't understand the server's response."
        case .network(let error):
            return "Couldn't reach the server: \(error.localizedDescription)"
        }
    }
}

enum APIClient {

    /// uvicorn's default local address (see backend/main.py's `uvicorn main:app --reload --port 8000`).
    static let baseURL = URL(string: "http://127.0.0.1:8000")!

    private static let encoder: JSONEncoder = {
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        return encoder
    }()

    private static let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        return decoder
    }()

    // -----------------------------------------------------------------
    // POST /upload-design
    // -----------------------------------------------------------------

    /// Uploads an inspiration image as multipart/form-data and returns the
    /// MLX-predicted garment type + confidence. Field name "file" must match
    /// `file: UploadFile = File(...)` in backend/main.py's upload_design().
    static func uploadDesign(image: UIImage) async throws -> UploadDesignResponse {
        guard let imageData = image.jpegData(compressionQuality: 0.85) else {
            throw APIError.server("Couldn't encode the selected image as JPEG.")
        }

        let boundary = "Boundary-\(UUID().uuidString)"
        var request = URLRequest(url: baseURL.appendingPathComponent("upload-design"))
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()
        body.append("--\(boundary)\r\n".utf8Data)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"design.jpg\"\r\n".utf8Data)
        body.append("Content-Type: image/jpeg\r\n\r\n".utf8Data)
        body.append(imageData)
        body.append("\r\n--\(boundary)--\r\n".utf8Data)
        request.httpBody = body

        return try await send(request)
    }

    // -----------------------------------------------------------------
    // POST /estimate-materials
    // -----------------------------------------------------------------

    static func estimateMaterials(
        garmentType: GarmentType,
        size: Size,
        fit: FitPreference
    ) async throws -> EstimateMaterialsResponse {
        struct Body: Encodable {
            let garmentType: GarmentType
            let size: Size
            let fitPreference: FitPreference
        }
        let request = try jsonRequest(
            path: "estimate-materials",
            body: Body(garmentType: garmentType, size: size, fitPreference: fit)
        )
        return try await send(request)
    }

    // -----------------------------------------------------------------
    // POST /generate-plan
    // -----------------------------------------------------------------

    static func generatePlan(
        garmentType: GarmentType,
        size: Size,
        fit: FitPreference,
        primaryMaterial: String
    ) async throws -> GeneratePlanResponse {
        struct Body: Encodable {
            let garmentType: GarmentType
            let size: Size
            let fitPreference: FitPreference
            let primaryMaterial: String
        }
        let request = try jsonRequest(
            path: "generate-plan",
            body: Body(garmentType: garmentType, size: size, fitPreference: fit, primaryMaterial: primaryMaterial)
        )
        return try await send(request)
    }

    // -----------------------------------------------------------------
    // Shared plumbing
    // -----------------------------------------------------------------

    private static func jsonRequest<Body: Encodable>(path: String, body: Body) throws -> URLRequest {
        var request = URLRequest(url: baseURL.appendingPathComponent(path))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        do {
            request.httpBody = try encoder.encode(body)
        } catch {
            throw APIError.decoding(error)
        }
        return request
    }

    /// Sends a request, checks the HTTP status, and decodes the response body.
    /// Non-2xx responses are surfaced as APIError.server using FastAPI's
    /// `{"detail": "..."}` error shape when present.
    private static func send<Response: Decodable>(_ request: URLRequest) async throws -> Response {
        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await URLSession.shared.data(for: request)
        } catch {
            throw APIError.network(error)
        }

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        guard (200..<300).contains(httpResponse.statusCode) else {
            let detail = (try? decoder.decode(APIErrorDetail.self, from: data))?.detail
            throw APIError.server(detail ?? "Server returned status \(httpResponse.statusCode).")
        }

        do {
            return try decoder.decode(Response.self, from: data)
        } catch {
            throw APIError.decoding(error)
        }
    }
}

private extension String {
    var utf8Data: Data { Data(self.utf8) }
}
