//
//  ContentView.swift
//  FitForm
//
//  App entry point. Wraps the three-screen flow in a NavigationStack so
//  UploadScreen → FitSelectorScreen → ResultScreen can push/pop cleanly.
//  No state lives here — each screen manages its own @State.
//

import SwiftUI

struct ContentView: View {
    var body: some View {
        NavigationStack {
            UploadScreen()
        }
    }
}

#Preview {
    ContentView()
}
