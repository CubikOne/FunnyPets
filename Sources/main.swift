import AppKit
import ServiceManagement

// MARK: - Colors & coats

func rgb(_ r: Int, _ g: Int, _ b: Int) -> NSColor {
    NSColor(srgbRed: CGFloat(r)/255, green: CGFloat(g)/255, blue: CGFloat(b)/255, alpha: 1)
}

let COL_OUTLINE = rgb(43, 29, 24)
let COL_WHITE   = rgb(252, 244, 232)
let COL_PINK    = rgb(247, 143, 158)
let COL_BLUSH   = rgb(250, 178, 162)
let COL_SHINE   = NSColor.white
let COL_STEAM   = NSColor(srgbRed: 0.72, green: 0.72, blue: 0.76, alpha: 0.9)
let COL_HEART   = rgb(244, 110, 130)
let COL_HOT     = rgb(236, 96, 72)
let COL_HOT_S   = rgb(198, 58, 42)
let COL_PAPER   = rgb(250, 248, 240)
let COL_PAPER_L = rgb(200, 196, 186)

// pixel-art paper roll (same cell grid as the cat): o outline, W paper, l line, h hole, B cat's paw
let ROLL_SPRITE = [
    ".ooo.",
    "oWWWo",
    "oWhWo",
    "oWWWo",
    "oWWWo",
    ".ooo.",
]
let STRIP_ROW  = "oWWWo"
let STRIP_LINE = "oWlWo"
let STRIP_TEAR = ".W.W."
let PAW_SPRITE = [
    ".ooo.",
    "oBBBo",
    ".ooo.",
]

// holiday hats, drawn on the cat's head (grid coords, bottom row anchored)
struct Hat { let grid: [String]; let pal: [Character: NSColor]; let col: Int; let bottomRow: Int }

let HAT_SANTA = Hat(
    grid: [
        "....oWWo...",
        "...oorroo..",
        "..orrrrrro.",
        ".orrrrrrro.",
        "oWWWWWWWWWo",
    ],
    pal: ["o": COL_OUTLINE, "r": rgb(206, 44, 58), "W": COL_WHITE],
    col: 5, bottomRow: 4)

let HAT_WITCH = Hat(
    grid: [
        "....okko.....",
        "....okko.....",
        "...okkkko....",
        "...oHHHHo....",
        ".ookkkkkkoo..",
        "okkkkkkkkkkko",
    ],
    pal: ["o": COL_OUTLINE, "k": rgb(74, 50, 100), "H": rgb(238, 146, 52)],
    col: 4, bottomRow: 4)

struct Solid { let title: String; let body: NSColor; let stripe: NSColor }

let SOLIDS: [Solid] = [
    Solid(title: "Рыжий",    body: rgb(240, 148, 54),  stripe: rgb(198, 104, 26)),
    Solid(title: "Серый",    body: rgb(154, 158, 170), stripe: rgb(110, 114, 126)),
    Solid(title: "Чёрный",   body: rgb(66, 60, 68),    stripe: rgb(44, 40, 48)),
    Solid(title: "Белый",    body: rgb(246, 242, 234), stripe: rgb(216, 208, 198)),
    Solid(title: "Кремовый", body: rgb(238, 208, 156), stripe: rgb(206, 162, 106)),
]

struct Pattern { let title: String; let grid: [String]; let gridHam: [String]; let pal: [Character: NSColor] }

let PATTERNS: [Pattern] = [
    Pattern(title: "Сиамский", grid: PATTERN_SIAMESE, gridHam: PATTERN_SIAMESE_HAM,
            pal: ["c": rgb(242, 232, 210), "d": rgb(88, 60, 48)]),
    Pattern(title: "Полосатый", grid: PATTERN_MACKEREL, gridHam: PATTERN_MACKEREL_HAM,
            pal: ["e": rgb(168, 172, 182), "f": rgb(106, 110, 122)]),
    Pattern(title: "Калико", grid: PATTERN_CALICO, gridHam: PATTERN_CALICO_HAM,
            pal: ["g": rgb(246, 242, 234), "h": rgb(238, 146, 52), "i": rgb(70, 64, 72)]),
    Pattern(title: "Смокинг", grid: PATTERN_TUXEDO, gridHam: PATTERN_TUXEDO_HAM,
            pal: ["j": rgb(52, 48, 56)]),
]

var isHamster: Bool { Prefs.species == "hamster" }
func baseFrame() -> [String] { isHamster ? HAM_BASE_F : FRAME_TAIL_DOWN }

// MARK: - Prefs

struct Reminder: Codable { var t: Date; var m: String }

final class Prefs {
    static let d = UserDefaults.standard
    static var species: String {    // cat | hamster
        get { d.string(forKey: "species") ?? "cat" }
        set { d.set(newValue, forKey: "species") }
    }
    static var coatType: String {   // solid | pattern | custom
        get { d.string(forKey: "coatType") ?? "solid" }
        set { d.set(newValue, forKey: "coatType") }
    }
    static var coatIdx: Int {
        get { d.object(forKey: "coatIdx") as? Int ?? 0 }
        set { d.set(newValue, forKey: "coatIdx") }
    }
    static var customPattern: Data? {
        get { d.data(forKey: "customPat") }
        set { d.set(newValue, forKey: "customPat") }
    }
    static var scale: Int {
        get { d.object(forKey: "scale") as? Int ?? 6 }
        set { d.set(newValue, forKey: "scale") }
    }
    static var stretchMin: Int {
        get { d.object(forKey: "stretchMin") as? Int ?? 45 }
        set { d.set(newValue, forKey: "stretchMin") }
    }
    static var sounds: Bool {
        get { d.object(forKey: "sounds") as? Bool ?? true }
        set { d.set(newValue, forKey: "sounds") }
    }
    static var topMost: Bool {
        get { d.object(forKey: "topMost") as? Bool ?? true }
        set { d.set(newValue, forKey: "topMost") }
    }
    static var huntEnabled: Bool {
        get { d.object(forKey: "huntEnabled") as? Bool ?? true }
        set { d.set(newValue, forKey: "huntEnabled") }
    }
    static var userName: String {
        get { d.string(forKey: "userName") ?? "" }
        set { d.set(newValue, forKey: "userName") }
    }
    static var catName: String {
        get { d.string(forKey: "catName") ?? "" }
        set { d.set(newValue, forKey: "catName") }
    }
    static var showCatName: Bool {
        get { d.object(forKey: "showCatName") as? Bool ?? false }
        set { d.set(newValue, forKey: "showCatName") }
    }
    static var fixedNote: String {
        get { d.string(forKey: "fixedNote") ?? "" }
        set { d.set(newValue, forKey: "fixedNote") }
    }
    static var reminders: [Reminder] {
        get {
            guard let data = d.data(forKey: "reminders") else { return [] }
            return (try? JSONDecoder().decode([Reminder].self, from: data)) ?? []
        }
        set { d.set(try? JSONEncoder().encode(newValue), forKey: "reminders") }
    }
    static var pos: NSPoint? {
        get {
            guard let x = d.object(forKey: "posX") as? Double,
                  let y = d.object(forKey: "posY") as? Double else { return nil }
            return NSPoint(x: x, y: y)
        }
        set {
            if let p = newValue { d.set(Double(p.x), forKey: "posX"); d.set(Double(p.y), forKey: "posY") }
        }
    }
}

// MARK: - Shared coloring

func colorFromHex(_ s: String) -> NSColor? {
    var h = s.trimmingCharacters(in: .whitespaces)
    if h.hasPrefix("#") { h.removeFirst() }
    guard h.count == 6, let v = UInt32(h, radix: 16) else { return nil }
    return NSColor(srgbRed: CGFloat((v >> 16) & 0xFF)/255,
                   green: CGFloat((v >> 8) & 0xFF)/255,
                   blue: CGFloat(v & 0xFF)/255, alpha: 1)
}

func hexFromColor(_ c: NSColor) -> String {
    let s = c.usingColorSpace(.sRGB) ?? c
    return String(format: "#%02X%02X%02X", Int(s.redComponent*255), Int(s.greenComponent*255), Int(s.blueComponent*255))
}

final class CoatEngine {
    var customOverrides: [Int: NSColor] = [:]
    var customFallback: NSColor = SOLIDS[0].body   // for animated pixels the pattern doesn't cover

    init() { loadCustom() }

    func loadCustom() {
        customOverrides = [:]
        customFallback = SOLIDS[0].body
        guard let data = Prefs.customPattern,
              let dict = try? JSONDecoder().decode([String: String].self, from: data) else { return }
        var counts: [String: Int] = [:]
        for (k, hex) in dict {
            let p = k.split(separator: ",")
            guard p.count == 2, let x = Int(p[0]), let y = Int(p[1]),
                  x >= 0, x < GRID_W, y >= 0, y < GRID_H,
                  let c = colorFromHex(hex) else { continue }
            customOverrides[y*GRID_W + x] = c
            counts[hex, default: 0] += 1
        }
        if let top = counts.max(by: { $0.value < $1.value }), let c = colorFromHex(top.key) {
            customFallback = c
        }
    }

    // dark fur around the eyes? then eyes need a light backing to stay visible
    func isDarkBody() -> Bool {
        guard let c = cellColor(EYE_LX, EYE_LY, "b", hot: false)?.usingColorSpace(.sRGB) else { return false }
        return (c.redComponent + c.greenComponent + c.blueComponent) / 3 < 0.35
    }

    // body color for accessories (paper-roll paw etc.)
    func accentBody() -> NSColor {
        cellColor(3, 14, "b", hot: false) ?? SOLIDS[0].body
    }

    // color for a body cell; nil = transparent
    func cellColor(_ x: Int, _ y: Int, _ ch: Character, hot: Bool) -> NSColor? {
        switch ch {
        case "o": return COL_OUTLINE
        case "p": break
        case "b", "s", "w": break
        default: return nil
        }
        if hot {
            switch ch {
            case "b": return COL_HOT
            case "s": return COL_HOT_S
            case "w": return COL_WHITE
            case "p": return COL_PINK
            default: return nil
            }
        }
        switch Prefs.coatType {
        case "pattern":
            let p = PATTERNS[min(Prefs.coatIdx, PATTERNS.count - 1)]
            if ch != "p" {
                let grid = isHamster ? p.gridHam : p.grid
                let pc = Array(grid[y])[x]
                if pc != ".", let c = p.pal[pc] { return c }
            }
        case "custom":
            if let c = customOverrides[y*GRID_W + x] { return c }
            if ch == "b" || ch == "s" { return customFallback }
        default: break
        }
        let solid = SOLIDS[min(Prefs.coatIdx, SOLIDS.count - 1)]
        switch ch {
        case "b": return Prefs.coatType == "solid" ? solid.body : SOLIDS[0].body
        case "s": return Prefs.coatType == "solid" ? solid.stripe : SOLIDS[0].stripe
        case "w": return COL_WHITE
        case "p": return COL_PINK
        default: return nil
        }
    }
}

// MARK: - State

enum CatState { case idle, knead, overheat, pet, sleep, drag, stretch, hunt, think }

struct HeartP { var x: CGFloat; var y: CGFloat; var age: CGFloat; var drift: CGFloat }

func secondsSince(_ t: CGEventType) -> Double {
    CGEventSource.secondsSinceLastEventType(.combinedSessionState, eventType: t)
}

// MARK: - Cat view

final class CatView: NSView {
    weak var controller: Controller?
    let coat: CoatEngine

    init(frame: NSRect, coat: CoatEngine) {
        self.coat = coat
        super.init(frame: frame)
    }
    required init?(coder: NSCoder) { fatalError() }

    var state: CatState = .idle
    var gaze: (dx: Int, dy: Int) = (0, 0)
    var blinkUntil: Date = .distantPast
    var nextBlink: Date = Date().addingTimeInterval(3)
    var tailUpUntil: Date = .distantPast
    var nextFlick: Date = Date().addingTimeInterval(4)
    var kneadFlip = false
    var kneadFlipAt: Date = .distantPast
    var hearts: [HeartP] = []
    var lastHeartAt: Date = .distantPast
    var steamPhase: CGFloat = 0
    var zzzPhase: CGFloat = 0
    var thinkPhase: CGFloat = 0
    var stretchAmount: CGFloat = 0
    var jelly: CGFloat = 0
    var jellyPhase: CGFloat = 0
    var jumpStarted: Date = .distantPast
    var paperLen: CGFloat = 0
    var paperPhase: CGFloat = 0
    var cheekFill: CGFloat = 0
    static let debugPaper = ProcessInfo.processInfo.environment["COMNYAN_PAPER"] != nil
    static let debugCheeks = ProcessInfo.processInfo.environment["COMNYAN_CHEEKS"] != nil

    // petting detection
    var petUntil: Date = .distantPast
    var lastPetX: CGFloat = 0
    var lastPetDir: Int = 0
    var petTurns: [Date] = []
    var purring = false

    // dragging
    var dragging = false
    var dragOffset = NSPoint.zero
    var lastDragPos = NSPoint.zero
    var dragVel: CGFloat = 0
    var pressedAt: Date = .distantPast
    var movedFar = false

    var S: CGFloat { CGFloat(Prefs.scale) }
    var marginX: CGFloat { 20 }
    var marginBottom: CGFloat { 20 }
    var catW: CGFloat { CGFloat(GRID_W) * S }
    var catH: CGFloat { CGFloat(GRID_H) * S }

    static func windowSize(scale: Int) -> NSSize {
        let s = CGFloat(scale)
        return NSSize(width: CGFloat(GRID_W)*s + 40, height: CGFloat(GRID_H)*s + 20 + s*10)
    }

    override var acceptsFirstResponder: Bool { true }
    override func acceptsFirstMouse(for event: NSEvent?) -> Bool { true }

    override func updateTrackingAreas() {
        super.updateTrackingAreas()
        trackingAreas.forEach(removeTrackingArea)
        addTrackingArea(NSTrackingArea(rect: bounds,
            options: [.mouseMoved, .mouseEnteredAndExited, .activeAlways],
            owner: self, userInfo: nil))
    }

    // MARK: tick

    func tick(now: Date) {
        guard let c = controller else { return }
        let tKey = secondsSince(.keyDown)
        let idleAll = min(secondsSince(.keyDown), secondsSince(.mouseMoved),
                          min(secondsSince(.leftMouseDown), secondsSince(.scrollWheel)))
        let scrolling = secondsSince(.scrollWheel) < 1.2

        // paper unroll (roll held at the cat's paw, strip feeds down to the floor)
        let paperMax = S * 7
        if secondsSince(.scrollWheel) < 0.25 {
            paperLen = min(paperMax, paperLen + S * 1.1)
            paperPhase += S * 0.45
        } else if secondsSince(.scrollWheel) > 2.5 {
            paperLen = max(0, paperLen - S * 0.35)
        }
        if Self.debugPaper { paperLen = paperMax; paperPhase += S * 0.45 }

        // state resolution (priority order)
        if dragging { state = .drag }
        else if c.stretchActiveUntil > now { state = .stretch }
        else if c.huntActive(now) { state = .hunt }
        else if petUntil > now { state = .pet }
        else if tKey < 1.2 { state = c.overheated ? .overheat : .knead }
        else if scrolling && paperLen > 2 { state = .knead }
        else if c.agentThinking { state = .think }
        else if idleAll > (c.nightNow ? 90 : 240) { state = .sleep }   // sleepier at night
        else { state = .idle }

        if state != .pet, purring { purring = false }

        let targetStretch: CGFloat = state == .stretch ? 1 : 0
        stretchAmount += (targetStretch - stretchAmount) * 0.18

        // gaze
        if state == .think {
            gaze = (1, -1)
        } else if let win = window {
            let mouse = NSEvent.mouseLocation
            let headCenter = NSPoint(x: win.frame.midX, y: win.frame.minY + marginBottom + catH*0.65)
            let dx = mouse.x - headCenter.x, dy = mouse.y - headCenter.y
            gaze.dx = dx < -30 ? -1 : (dx > 30 ? 1 : 0)
            gaze.dy = dy < -60 ? 1 : (dy > 60 ? -1 : 0)
        }

        // hamster cheeks fill while typing, deflate slowly
        if isHamster {
            if state == .knead || state == .overheat {
                cheekFill = min(1, cheekFill + 0.012)
            } else {
                cheekFill = max(0, cheekFill - 0.004)
            }
            if Self.debugCheeks { cheekFill = 1 }
        } else {
            cheekFill = 0
        }

        // blink
        if state != .hunt, now > nextBlink {
            blinkUntil = now.addingTimeInterval(0.15)
            nextBlink = now.addingTimeInterval(Double.random(in: 2.5...6))
        }
        // tail flick (cat only)
        if state == .idle, !isHamster, now > nextFlick {
            tailUpUntil = now.addingTimeInterval(0.6)
            nextFlick = now.addingTimeInterval(Double.random(in: 3...8))
        }
        // knead animation
        let flipInterval = state == .overheat ? 0.16 : 0.26
        if (state == .knead || state == .overheat), now.timeIntervalSince(kneadFlipAt) > flipInterval {
            kneadFlip.toggle(); kneadFlipAt = now
        }
        // hearts
        if state == .pet, now.timeIntervalSince(lastHeartAt) > 0.35 {
            hearts.append(HeartP(x: catW*0.5 + CGFloat.random(in: -30...30),
                                 y: catH*0.9, age: 0, drift: CGFloat.random(in: -8...8)))
            lastHeartAt = now
        }
        for i in hearts.indices { hearts[i].age += 0.033; hearts[i].y += 0.8; hearts[i].x += hearts[i].drift*0.008 }
        hearts.removeAll { $0.age > 1.6 }

        steamPhase += 0.06
        zzzPhase += 0.02
        thinkPhase += 0.05

        // hunt wiggle
        if state == .hunt { jelly = max(jelly, 0.06); jellyPhase += 0.35 }

        if !dragging, state != .hunt { jelly *= 0.95 }
        jellyPhase += 0.18
        dragVel *= 0.93

        needsDisplay = true
    }

    // MARK: mouse

    override func mouseExited(with event: NSEvent) { lastPetDir = 0 }

    override func mouseMoved(with event: NSEvent) {
        let p = convert(event.locationInWindow, from: nil)
        let headRect = NSRect(x: marginX + catW*0.1, y: marginBottom + catH*0.35,
                              width: catW*0.8, height: catH*0.75)
        guard headRect.contains(p) else { lastPetDir = 0; return }
        let dx = p.x - lastPetX
        lastPetX = p.x
        guard abs(dx) > 1.5 else { return }
        let dir = dx > 0 ? 1 : -1
        let now = Date()
        if dir != lastPetDir, lastPetDir != 0 {
            petTurns.append(now)
            petTurns.removeAll { now.timeIntervalSince($0) > 1.5 }
            if petTurns.count >= 3 {
                petUntil = now.addingTimeInterval(1.2)
                if !purring {
                    purring = true
                    controller?.play("Purr")
                }
            }
        }
        lastPetDir = dir
    }

    override func mouseDown(with event: NSEvent) {
        pressedAt = Date()
        movedFar = false
        dragging = true
        let mouse = NSEvent.mouseLocation
        if let win = window {
            dragOffset = NSPoint(x: mouse.x - win.frame.origin.x, y: mouse.y - win.frame.origin.y)
            lastDragPos = mouse
        }
    }

    override func mouseDragged(with event: NSEvent) {
        guard let win = window else { return }
        let mouse = NSEvent.mouseLocation
        win.setFrameOrigin(NSPoint(x: mouse.x - dragOffset.x, y: mouse.y - dragOffset.y))
        let v = hypot(mouse.x - lastDragPos.x, mouse.y - lastDragPos.y)
        dragVel = min(1, dragVel + v/120)
        if v > 4 { movedFar = true }
        jelly = min(0.16, dragVel * 0.16)
        lastDragPos = mouse
    }

    override func mouseUp(with event: NSEvent) {
        dragging = false
        jelly = max(jelly, dragVel * 0.14)
        if !movedFar, Date().timeIntervalSince(pressedAt) < 0.35 {
            if controller?.peeking == true {
                controller?.unpeek()
            } else if let c = controller, c.stretchActiveUntil > Date() {
                c.stretchActiveUntil = .distantPast
            } else {
                controller?.meow()
            }
            return
        }
        controller?.settleAfterDrag()
    }

    override func rightMouseDown(with event: NSEvent) {
        if let menu = controller?.buildMenu() {
            NSMenu.popUpContextMenu(menu, with: event, for: self)
        }
    }

    // MARK: drawing

    override func draw(_ dirtyRect: NSRect) {
        guard let ctx = NSGraphicsContext.current?.cgContext else { return }
        let now = Date()
        let hot = state == .overheat

        if paperLen > 3 { drawPaper(ctx) }  // under the cat

        let ham = isHamster
        let frame: [String]
        switch state {
        case .knead, .overheat:
            frame = kneadFlip ? (ham ? HAM_KNEAD_0 : FRAME_KNEAD_0) : (ham ? HAM_KNEAD_1 : FRAME_KNEAD_1)
        default:
            frame = ham ? HAM_BASE_F : (tailUpUntil > now ? FRAME_TAIL_UP : FRAME_TAIL_DOWN)
        }

        ctx.saveGState()
        let anchorX = marginX + catW/2, anchorY = marginBottom
        let wob = jelly * sin(jellyPhase)
        let grow = 1 + stretchAmount * 0.45
        var sx = (1 + wob) * grow
        var sy = (1 - wob) * grow
        if dragging { sy *= 1 + dragVel*0.25; sx *= 1 - dragVel*0.12 }
        if state == .hunt { sy *= 0.88; sx *= 1.06 }   // crouch
        var hopY: CGFloat = 0
        let hopT = now.timeIntervalSince(jumpStarted)
        if hopT < 0.9 { hopY = abs(sin(CGFloat(hopT) * .pi * 2.2)) * 26 * CGFloat(1 - hopT/0.9) }
        ctx.translateBy(x: anchorX, y: anchorY + hopY)
        ctx.scaleBy(x: sx, y: sy)
        ctx.translateBy(x: -catW/2, y: 0)

        for (row, line) in frame.enumerated() {
            let y = CGFloat(GRID_H - 1 - row) * S
            for (col, ch) in line.enumerated() {
                guard let c = coat.cellColor(col, row, ch, hot: hot) else { continue }
                c.setFill()
                ctx.fill(CGRect(x: CGFloat(col)*S, y: y, width: S, height: S))
            }
        }

        if ham { drawCheeks(ctx, hot: hot) }

        if let hat = controller?.hat {
            for (r, line) in hat.grid.enumerated() {
                let gy = hat.bottomRow - (hat.grid.count - 1) + r
                for (c, ch) in line.enumerated() {
                    guard let col = hat.pal[ch] else { continue }
                    col.setFill()
                    ctx.fill(px(hat.col + c, gy))
                }
            }
        }

        let eyesClosed = state == .sleep || blinkUntil > now
        let eyesHappy = state == .pet || state == .stretch
        drawEyes(ctx, closed: eyesClosed && state != .hunt, happy: eyesHappy, wide: state == .hunt)

        if state == .pet {
            COL_BLUSH.setFill()
            for ex in [3, 17] { ctx.fill(px(ex, 11)); ctx.fill(px(ex+1, 11)) }
        }
        ctx.restoreGState()

        if hot { drawSteam(ctx) }
        if state == .sleep { drawZzz(ctx) }
        if state == .think { drawThinkDots(ctx) }
        for h in hearts { drawHeart(ctx, h) }
        if Prefs.showCatName, !Prefs.catName.isEmpty { drawNamePlate() }
    }

    func px(_ x: Int, _ y: Int) -> CGRect {
        CGRect(x: CGFloat(x)*S, y: CGFloat(GRID_H - 1 - y)*S, width: S, height: S)
    }

    func drawEyes(_ ctx: CGContext, closed: Bool, happy: Bool, wide: Bool) {
        let dark = coat.isDarkBody()
        let ink = dark ? COL_WHITE : COL_OUTLINE
        for (ex, ey) in [(EYE_LX, EYE_LY), (EYE_RX, EYE_RY)] {
            if happy {
                ink.setFill()
                ctx.fill(px(ex-1, ey+1)); ctx.fill(px(ex, ey)); ctx.fill(px(ex+1, ey+1))
            } else if closed {
                ink.setFill()
                ctx.fill(px(ex, ey+1)); ctx.fill(px(ex+1, ey+1))
            } else if dark {
                // big light eye, pupil moves inside it
                COL_WHITE.setFill()
                ctx.fill(px(ex, ey)); ctx.fill(px(ex+1, ey))
                ctx.fill(px(ex, ey+1)); ctx.fill(px(ex+1, ey+1))
                COL_OUTLINE.setFill()
                let pxx = ex + (gaze.dx > 0 ? 1 : 0)
                let pyy = ey + (gaze.dy > 0 ? 1 : 0)
                ctx.fill(px(pxx, pyy))
                if wide { ctx.fill(px(pxx == ex ? ex+1 : ex, pyy)) }
            } else {
                COL_OUTLINE.setFill()
                let x = ex + gaze.dx, y = ey + gaze.dy
                ctx.fill(px(x, y)); ctx.fill(px(x+1, y))
                ctx.fill(px(x, y+1)); ctx.fill(px(x+1, y+1))
                if !wide {
                    COL_SHINE.setFill()
                    ctx.fill(px(x, y))
                }
            }
        }
    }

    // draws a small pixel grid (same cell size as the cat sprite)
    func drawPixelGrid(_ ctx: CGContext, _ grid: [String], x: CGFloat, top: CGFloat, paw: NSColor) {
        for (r, line) in grid.enumerated() {
            for (c, ch) in line.enumerated() {
                let color: NSColor?
                switch ch {
                case "o": color = COL_OUTLINE
                case "W": color = COL_PAPER
                case "l": color = COL_PAPER_L
                case "h": color = rgb(150, 146, 136)
                case "B": color = paw
                default: color = nil
                }
                guard let col = color else { continue }
                col.setFill()
                ctx.fill(CGRect(x: x + CGFloat(c)*S, y: top - CGFloat(r+1)*S, width: S, height: S))
            }
        }
    }

    // hamster cheek pouches: fill up while typing, deflate slowly
    func drawCheeks(_ ctx: CGContext, hot: Bool) {
        let level = cheekFill > 0.7 ? 2 : (cheekFill > 0.25 ? 1 : 0)
        guard level > 0 else { return }
        let fill = hot ? COL_BLUSH : COL_WHITE
        var white: [(Int, Int)]
        var ring: [(Int, Int)]
        var pink: [(Int, Int)] = []
        if level == 1 {
            white = [(2, 10), (3, 10), (2, 11), (3, 11)]
            ring  = [(2, 9), (3, 9), (4, 10), (4, 11), (2, 12), (3, 12)]
        } else {
            white = [(2, 10), (3, 10), (4, 10), (2, 11), (3, 11), (4, 11), (2, 12), (3, 12)]
            ring  = [(2, 9), (3, 9), (4, 9), (5, 10), (5, 11), (4, 12), (2, 13), (3, 13)]
            pink  = [(3, 11)]
        }
        let mirror: (Int) -> Int = { 21 - $0 }
        COL_OUTLINE.setFill()
        for (x, y) in ring { ctx.fill(px(x, y)); ctx.fill(px(mirror(x), y)) }
        fill.setFill()
        for (x, y) in white { ctx.fill(px(x, y)); ctx.fill(px(mirror(x), y)) }
        COL_PINK.setFill()
        for (x, y) in pink { ctx.fill(px(x, y)); ctx.fill(px(mirror(x), y)) }
    }

    func drawPaper(_ ctx: CGContext) {
        // pixel paper roll like comnyang: held by the cat's paw, strip feeds down to the floor
        let pawC = coat.accentBody()
        let ox = S * 0.5
        let rollTop = marginBottom + S * 13          // roll spans rows 13..7 above ground
        drawPixelGrid(ctx, ROLL_SPRITE, x: ox, top: rollTop, paw: pawC)

        // hanging strip: rows appear as the paper dispenses, lines scroll down
        let stripTop = rollTop - S * 6
        let rows = min(7, Int(paperLen / S))
        let phaseRow = Int(paperPhase / S)
        for i in 0..<rows {
            let row: String
            if i == rows - 1 {
                row = STRIP_TEAR
            } else if ((i - phaseRow) % 3 + 3) % 3 == 1 {
                row = STRIP_LINE
            } else {
                row = STRIP_ROW
            }
            drawPixelGrid(ctx, [row], x: ox, top: stripTop - CGFloat(i)*S, paw: pawC)
        }

        // the cat's paw resting on the roll, reaching from the body
        let bob = (state == .knead || secondsSince(.scrollWheel) < 0.25) && kneadFlip ? S : 0
        drawPixelGrid(ctx, PAW_SPRITE, x: ox + S*3, top: rollTop + S*1 - bob, paw: pawC)
    }

    func drawSteam(_ ctx: CGContext) {
        COL_STEAM.setFill()
        let baseX = marginX + catW/2
        for i in 0..<3 {
            let ph = steamPhase + CGFloat(i) * 2.1
            let rise = (ph.truncatingRemainder(dividingBy: 6)) / 6
            let y = marginBottom + catH + rise * S * 5
            let x = baseX + CGFloat(i - 1) * S * 3.2 + sin(ph) * 3
            let r = S * (0.8 + rise * 0.8)
            ctx.setAlpha((1 - rise) * 0.85)
            ctx.fillEllipse(in: CGRect(x: x - r, y: y - r, width: r*2, height: r*2))
        }
        ctx.setAlpha(1)
    }

    func drawZzz(_ ctx: CGContext) {
        let baseX = marginX + catW * 0.72
        let baseY = marginBottom + catH * 0.95
        for i in 0..<3 {
            let ph = (zzzPhase + CGFloat(i) * 0.9).truncatingRemainder(dividingBy: 2.7)
            let t = ph / 2.7
            let size = 9 + CGFloat(i) * 3
            let attrs: [NSAttributedString.Key: Any] = [
                .font: NSFont.monospacedSystemFont(ofSize: size, weight: .bold),
                .foregroundColor: NSColor(srgbRed: 0.45, green: 0.5, blue: 0.65, alpha: 1 - t*0.8),
            ]
            ("z" as NSString).draw(at: NSPoint(x: baseX + t*22 + CGFloat(i)*6,
                                               y: baseY + t*26 + CGFloat(i)*4), withAttributes: attrs)
        }
    }

    func drawThinkDots(_ ctx: CGContext) {
        let baseX = marginX + catW * 0.8
        let baseY = marginBottom + catH + S
        for i in 0..<3 {
            let a = 0.25 + 0.75 * (sin(thinkPhase * 3 - CGFloat(i) * 0.9) + 1) / 2
            NSColor(srgbRed: 0.5, green: 0.55, blue: 0.7, alpha: a).setFill()
            let r = S * 0.55
            ctx.fillEllipse(in: CGRect(x: baseX + CGFloat(i) * S * 1.6, y: baseY + CGFloat(i) * S * 0.9,
                                       width: r*2, height: r*2))
        }
    }

    func drawHeart(_ ctx: CGContext, _ h: HeartP) {
        ctx.setAlpha(max(0, 1 - h.age/1.6))
        COL_HEART.setFill()
        let u: CGFloat = 3
        let map = [".#.#.", "#####", ".###.", "..#.."]
        let x0 = marginX + h.x - u*2.5, y0 = marginBottom + h.y
        for (r, line) in map.enumerated() {
            for (c, ch) in line.enumerated() where ch == "#" {
                ctx.fill(CGRect(x: x0 + CGFloat(c)*u, y: y0 + CGFloat(map.count - r)*u, width: u, height: u))
            }
        }
        ctx.setAlpha(1)
    }

    func drawNamePlate() {
        let name = Prefs.catName
        let attrs: [NSAttributedString.Key: Any] = [
            .font: NSFont.monospacedSystemFont(ofSize: 9, weight: .semibold),
            .foregroundColor: NSColor.white,
        ]
        let ts = (name as NSString).size(withAttributes: attrs)
        let w = ts.width + 10, h = ts.height + 3
        let rect = NSRect(x: marginX + catW/2 - w/2, y: 2, width: w, height: h)
        let path = NSBezierPath(roundedRect: rect, xRadius: 4, yRadius: 4)
        NSColor(srgbRed: 0.1, green: 0.08, blue: 0.09, alpha: 0.62).setFill()
        path.fill()
        (name as NSString).draw(at: NSPoint(x: rect.minX + 5, y: rect.minY + 1.5), withAttributes: attrs)
    }
}

// MARK: - Bubble (click-through window)

final class BubbleView: NSView {
    var text: String = "" { didSet { needsDisplay = true } }
    static let font = NSFont.monospacedSystemFont(ofSize: 12, weight: .semibold)

    static func size(for text: String) -> NSSize {
        let s = (text as NSString).size(withAttributes: [.font: font])
        return NSSize(width: ceil(s.width) + 24, height: ceil(s.height) + 20)
    }

    override func draw(_ dirtyRect: NSRect) {
        let rect = NSRect(x: 1, y: 9, width: bounds.width - 2, height: bounds.height - 10)
        let path = NSBezierPath(roundedRect: rect, xRadius: 7, yRadius: 7)
        let tail = NSBezierPath()
        tail.move(to: NSPoint(x: bounds.midX - 6, y: 10))
        tail.line(to: NSPoint(x: bounds.midX, y: 1))
        tail.line(to: NSPoint(x: bounds.midX + 6, y: 10))
        tail.close()
        path.append(tail)
        NSColor(srgbRed: 1, green: 0.99, blue: 0.96, alpha: 0.97).setFill()
        path.fill()
        COL_OUTLINE.setStroke()
        path.lineWidth = 1.5
        path.stroke()
        let attrs: [NSAttributedString.Key: Any] = [.font: Self.font, .foregroundColor: COL_OUTLINE]
        let ts = (text as NSString).size(withAttributes: attrs)
        (text as NSString).draw(at: NSPoint(x: (bounds.width - ts.width)/2,
                                            y: 9 + (rect.height - ts.height)/2), withAttributes: attrs)
    }
}

// MARK: - Controller

final class Controller: NSObject, NSApplicationDelegate {
    var window: NSWindow!
    var catView: CatView!
    var bubbleWindow: NSWindow!
    var bubbleView: BubbleView!
    var statusItem: NSStatusItem!
    var timer: Timer?
    let coat = CoatEngine()

    var message = ""
    var messageUntil: Date = .distantPast

    var lastStretchAt = Date()
    var stretchActiveUntil: Date = .distantPast

    var pomoEnd: Date?
    var pomoIsBreak = false
    var pomoWork = 25, pomoBreak = 5

    var keyEvents: [Date] = []
    var overheated = false
    var hotSince: Date?

    // hunt — triggered by shaking the mouse in place (the same gesture that grows the macOS cursor)
    var prevMouse = NSEvent.mouseLocation
    var lastDirX = 0, lastDirY = 0
    var reversalsX: [Date] = [], reversalsY: [Date] = []
    var huntStalkUntil: Date = .distantPast
    var huntCooldownUntil: Date = .distantPast
    var pounce: (from: NSPoint, to: NSPoint, start: Date)?
    var pounceCount = 0

    // agent
    var agentThinking = false
    var lastAgentState = ""
    let agentFile = (NSString(string: "~/.comnyan/agent")).expandingTildeInPath

    // peek
    var peeking = false

    // walks
    var nextWalkAt = Date().addingTimeInterval(Double.random(in: 180...420))
    var walkHopsLeft = 0
    var walkStepX: CGFloat = 0
    var walkHop: (from: NSPoint, to: NSPoint, start: Date)?

    // time of day / holidays
    var lastPeriod = -1
    var nightNow = false
    var hat: Hat?

    var tickCount = 0

    func name(_ suffix: String) -> String {
        Prefs.userName.isEmpty ? suffix : "\(Prefs.userName), \(suffix)"
    }

    func dayPeriod(_ date: Date) -> Int {   // 0 night, 1 morning, 2 day, 3 evening
        switch Calendar.current.component(.hour, from: date) {
        case 5..<11: return 1
        case 11..<17: return 2
        case 17..<23: return 3
        default: return 0
        }
    }

    func computeHat() {
        if let e = ProcessInfo.processInfo.environment["COMNYAN_HAT"] {
            hat = e == "ny" ? HAT_SANTA : e == "hw" ? HAT_WITCH : nil
            return
        }
        let c = Calendar.current.dateComponents([.month, .day], from: Date())
        if (c.month == 12 && c.day! >= 15) || (c.month == 1 && c.day! <= 7) { hat = HAT_SANTA }
        else if c.month == 10 && c.day! >= 24 { hat = HAT_WITCH }
        else { hat = nil }
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        setupWindows()
        setupStatusItem()
        computeHat()
        lastPeriod = dayPeriod(Date())
        nightNow = lastPeriod == 0
        timer = Timer.scheduledTimer(withTimeInterval: 1.0/30, repeats: true) { [weak self] _ in self?.tick() }
        RunLoop.main.add(timer!, forMode: .common)
        let greeting: String
        switch lastPeriod {
        case 1: greeting = name("доброе утро! ☀️")
        case 3: greeting = name("добрый вечер! Мяу")
        case 0: greeting = name("мяу… не пора ли спать? 🌙")
        default: greeting = name("мяу! Я тут :3")
        }
        showMessage(greeting, for: 5)
        catView.jumpStarted = Date()

        if let p = ProcessInfo.processInfo.environment["COMNYAN_IMPORT"] {
            importCoat(from: URL(fileURLWithPath: p))
        }
        if let path = ProcessInfo.processInfo.environment["COMNYAN_SNAPSHOT"] {
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) { [self] in
                snapshot(view: catView, to: path + "-cat.png")
                snapshot(view: bubbleView, to: path + "-bubble.png")
            }
        }
    }

    func snapshot(view: NSView, to path: String) {
        guard view.bounds.width > 1,
              let rep = view.bitmapImageRepForCachingDisplay(in: view.bounds) else { return }
        view.cacheDisplay(in: view.bounds, to: rep)
        try? rep.representation(using: .png, properties: [:])?.write(to: URL(fileURLWithPath: path))
    }

    func setupWindows() {
        let size = CatView.windowSize(scale: Prefs.scale)
        window = NSWindow(contentRect: NSRect(origin: .zero, size: size),
                          styleMask: [.borderless], backing: .buffered, defer: false)
        window.isOpaque = false
        window.backgroundColor = .clear
        window.hasShadow = false
        window.level = Prefs.topMost ? .floating : .normal
        window.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        window.acceptsMouseMovedEvents = true
        catView = CatView(frame: NSRect(origin: .zero, size: size), coat: coat)
        catView.controller = self
        window.contentView = catView

        if let p = Prefs.pos, screenContains(p) {
            window.setFrameOrigin(p)
        } else if let scr = NSScreen.main {
            let v = scr.visibleFrame
            window.setFrameOrigin(NSPoint(x: v.maxX - size.width - 60, y: v.minY + 4))
        }
        window.orderFrontRegardless()

        bubbleWindow = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 10, height: 10),
                                styleMask: [.borderless], backing: .buffered, defer: false)
        bubbleWindow.isOpaque = false
        bubbleWindow.backgroundColor = .clear
        bubbleWindow.hasShadow = false
        bubbleWindow.ignoresMouseEvents = true
        bubbleWindow.level = window.level
        bubbleWindow.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        bubbleView = BubbleView(frame: .zero)
        bubbleWindow.contentView = bubbleView
    }

    func screenContains(_ p: NSPoint) -> Bool {
        // generous inset so a peeked (half-offscreen) position survives restart
        NSScreen.screens.contains { $0.visibleFrame.insetBy(dx: -160, dy: -60).contains(p) }
    }

    // MARK: status icon — pixel cat head

    func statusIcon() -> NSImage {
        let rows = 0...12, cols = 1...20
        let w = CGFloat(cols.count), h = CGFloat(rows.count)
        let frame = baseFrame()
        let img = NSImage(size: NSSize(width: w, height: h), flipped: false) { [coat] _ in
            guard let ctx = NSGraphicsContext.current?.cgContext else { return false }
            for row in rows {
                let line = Array(frame[row])
                for col in cols {
                    guard let c = coat.cellColor(col, row, line[col], hot: false) else { continue }
                    c.setFill()
                    ctx.fill(CGRect(x: CGFloat(col - cols.lowerBound), y: h - 1 - CGFloat(row - rows.lowerBound),
                                    width: 1, height: 1))
                }
            }
            // eyes
            let dark = coat.isDarkBody()
            for (ex, ey) in [(EYE_LX, EYE_LY), (EYE_RX, EYE_RY)] {
                let r = CGRect(x: CGFloat(ex - 1), y: h - 2 - CGFloat(ey), width: 2, height: 2)
                if dark {
                    COL_WHITE.setFill(); ctx.fill(r)
                    COL_OUTLINE.setFill()
                    ctx.fill(CGRect(x: r.minX + 1, y: r.minY, width: 1, height: 1))
                } else {
                    COL_OUTLINE.setFill(); ctx.fill(r)
                }
            }
            return true
        }
        return img
    }

    func setupStatusItem() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        statusItem.button?.image = statusIcon()
        statusItem.menu = buildMenu()
    }

    func refreshUI() {
        statusItem.button?.image = statusIcon()
        statusItem.menu = buildMenu()
    }

    // MARK: menu

    func buildMenu() -> NSMenu {
        let menu = NSMenu()

        let petMenu = NSMenu()
        for (t, s) in [("Кот 🐈", "cat"), ("Хомяк 🐹", "hamster")] {
            let it = NSMenuItem(title: t, action: #selector(setSpecies(_:)), keyEquivalent: "")
            it.target = self
            it.representedObject = s
            it.state = Prefs.species == s ? .on : .off
            petMenu.addItem(it)
        }
        menu.addItem(withSubmenu: petMenu, title: "Питомец")

        let coatMenu = NSMenu()
        for (i, c) in SOLIDS.enumerated() {
            let it = NSMenuItem(title: c.title, action: #selector(setSolid(_:)), keyEquivalent: "")
            it.target = self; it.tag = i
            it.state = (Prefs.coatType == "solid" && Prefs.coatIdx == i) ? .on : .off
            coatMenu.addItem(it)
        }
        coatMenu.addItem(.separator())
        for (i, p) in PATTERNS.enumerated() {
            let it = NSMenuItem(title: p.title, action: #selector(setPattern(_:)), keyEquivalent: "")
            it.target = self; it.tag = i
            it.state = (Prefs.coatType == "pattern" && Prefs.coatIdx == i) ? .on : .off
            coatMenu.addItem(it)
        }
        coatMenu.addItem(.separator())
        let custom = NSMenuItem(title: "Импорт окраса (JSON/PNG)…", action: #selector(importCoat as () -> Void), keyEquivalent: "")
        custom.target = self
        custom.state = Prefs.coatType == "custom" ? .on : .off
        coatMenu.addItem(custom)
        let tmpl = NSMenuItem(title: "Сохранить шаблон PNG…", action: #selector(exportTemplate), keyEquivalent: "")
        tmpl.target = self
        coatMenu.addItem(tmpl)
        menu.addItem(withSubmenu: coatMenu, title: "Окрас")

        let sizeMenu = NSMenu()
        for (t, s) in [("Маленький", 4), ("Средний", 6), ("Большой", 8)] {
            let it = NSMenuItem(title: t, action: #selector(setScale(_:)), keyEquivalent: "")
            it.target = self; it.tag = s; it.state = Prefs.scale == s ? .on : .off
            sizeMenu.addItem(it)
        }
        menu.addItem(withSubmenu: sizeMenu, title: "Размер")

        menu.addItem(.separator())

        let pomoMenu = NSMenu()
        if pomoEnd == nil {
            for (t, w, b) in [("Старт 25+5", 25, 5), ("Старт 50+10", 50, 10)] {
                let it = NSMenuItem(title: t, action: #selector(pomoStart(_:)), keyEquivalent: "")
                it.target = self; it.tag = w * 100 + b
                pomoMenu.addItem(it)
            }
        } else {
            let it = NSMenuItem(title: "Стоп", action: #selector(pomoStop), keyEquivalent: "")
            it.target = self
            pomoMenu.addItem(it)
        }
        menu.addItem(withSubmenu: pomoMenu, title: "🍅 Помодоро")

        let remMenu = NSMenu()
        let addRem = NSMenuItem(title: "Добавить…", action: #selector(addReminder), keyEquivalent: "")
        addRem.target = self
        remMenu.addItem(addRem)
        let rems = Prefs.reminders
        if !rems.isEmpty {
            remMenu.addItem(.separator())
            let df = DateFormatter(); df.dateFormat = "HH:mm"
            for (i, r) in rems.enumerated() {
                let it = NSMenuItem(title: "✕ \(df.string(from: r.t)) — \(r.m)",
                                    action: #selector(removeReminder(_:)), keyEquivalent: "")
                it.target = self; it.tag = i
                remMenu.addItem(it)
            }
        }
        menu.addItem(withSubmenu: remMenu, title: "⏰ Напоминания")

        let stretchMenu = NSMenu()
        for (t, m) in [("Выкл", 0), ("Каждые 30 мин", 30), ("Каждые 45 мин", 45), ("Каждый час", 60)] {
            let it = NSMenuItem(title: t, action: #selector(setStretch(_:)), keyEquivalent: "")
            it.target = self; it.tag = m; it.state = Prefs.stretchMin == m ? .on : .off
            stretchMenu.addItem(it)
        }
        menu.addItem(withSubmenu: stretchMenu, title: "🧘 Разминка")

        let noteTitle = Prefs.fixedNote.isEmpty ? "Закрепить заметку…" : "Заметка: «\(Prefs.fixedNote)»…"
        let note = NSMenuItem(title: noteTitle, action: #selector(editNote), keyEquivalent: "")
        note.target = self
        menu.addItem(note)

        menu.addItem(.separator())

        let nameMenu = NSMenu()
        let myName = NSMenuItem(title: Prefs.userName.isEmpty ? "Представиться коту…" : "Я — \(Prefs.userName)…",
                                action: #selector(editUserName), keyEquivalent: "")
        myName.target = self
        nameMenu.addItem(myName)
        let catName = NSMenuItem(title: Prefs.catName.isEmpty ? "Назвать кота…" : "Кот — \(Prefs.catName)…",
                                 action: #selector(editCatName), keyEquivalent: "")
        catName.target = self
        nameMenu.addItem(catName)
        let showName = NSMenuItem(title: "Показывать имя кота", action: #selector(toggleShowName), keyEquivalent: "")
        showName.target = self; showName.state = Prefs.showCatName ? .on : .off
        nameMenu.addItem(showName)
        menu.addItem(withSubmenu: nameMenu, title: "Имена")

        menu.addItem(.separator())

        let hunt = NSMenuItem(title: "Охота за курсором", action: #selector(toggleHunt), keyEquivalent: "")
        hunt.target = self; hunt.state = Prefs.huntEnabled ? .on : .off
        menu.addItem(hunt)

        let peek = NSMenuItem(title: peeking ? "Выглянуть" : "Спрятаться за край",
                              action: peeking ? #selector(unpeek) : #selector(peekNearestEdge), keyEquivalent: "")
        peek.target = self
        menu.addItem(peek)

        let snd = NSMenuItem(title: "Звуки", action: #selector(toggleSounds), keyEquivalent: "")
        snd.target = self; snd.state = Prefs.sounds ? .on : .off
        menu.addItem(snd)

        let top = NSMenuItem(title: "Поверх всех окон", action: #selector(toggleTop), keyEquivalent: "")
        top.target = self; top.state = Prefs.topMost ? .on : .off
        menu.addItem(top)

        if #available(macOS 13.0, *) {
            let li = NSMenuItem(title: "Запускать при входе", action: #selector(toggleLogin), keyEquivalent: "")
            li.target = self; li.state = SMAppService.mainApp.status == .enabled ? .on : .off
            menu.addItem(li)
        }

        menu.addItem(.separator())
        menu.addItem(NSMenuItem(title: "Выход", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q"))
        return menu
    }

    // MARK: menu actions

    @objc func setSpecies(_ s: NSMenuItem) {
        Prefs.species = s.representedObject as? String ?? "cat"
        showMessage(isHamster ? "Пип! Я хомяк 🐹" : name("мяу! Снова кот :3"), for: 4)
        catView.jumpStarted = Date()
        refreshUI()
    }

    @objc func setSolid(_ s: NSMenuItem) { Prefs.coatType = "solid"; Prefs.coatIdx = s.tag; refreshUI() }
    @objc func setPattern(_ s: NSMenuItem) { Prefs.coatType = "pattern"; Prefs.coatIdx = s.tag; refreshUI() }

    @objc func setScale(_ sender: NSMenuItem) {
        Prefs.scale = sender.tag
        let old = window.frame
        let size = CatView.windowSize(scale: sender.tag)
        window.setFrame(NSRect(origin: NSPoint(x: old.midX - size.width/2, y: old.minY), size: size), display: true)
        catView.frame = NSRect(origin: .zero, size: size)
        catView.updateTrackingAreas()
        Prefs.pos = window.frame.origin
        refreshUI()
    }

    @objc func setStretch(_ sender: NSMenuItem) {
        Prefs.stretchMin = sender.tag
        lastStretchAt = Date()
        refreshUI()
    }

    @objc func toggleSounds() { Prefs.sounds.toggle(); refreshUI() }
    @objc func toggleHunt() { Prefs.huntEnabled.toggle(); refreshUI() }
    @objc func toggleShowName() { Prefs.showCatName.toggle(); refreshUI() }

    @objc func toggleTop() {
        Prefs.topMost.toggle()
        window.level = Prefs.topMost ? .floating : .normal
        bubbleWindow.level = window.level
        refreshUI()
    }

    @objc func toggleLogin() {
        if #available(macOS 13.0, *) {
            let svc = SMAppService.mainApp
            do {
                if svc.status == .enabled { try svc.unregister() } else { try svc.register() }
            } catch {
                showMessage("Не вышло: \(error.localizedDescription)", for: 4)
            }
            refreshUI()
        }
    }

    @objc func pomoStart(_ sender: NSMenuItem) {
        pomoWork = sender.tag / 100
        pomoBreak = sender.tag % 100
        pomoEnd = Date().addingTimeInterval(Double(pomoWork) * 60)
        pomoIsBreak = false
        showMessage(name("фокус \(pomoWork) минут. Погнали!"), for: 4)
        refreshUI()
    }

    @objc func pomoStop() {
        pomoEnd = nil
        showMessage("Помодоро выключен", for: 3)
        refreshUI()
    }

    // MARK: dialogs

    func ask(_ title: String, _ info: String, text: String, timeField: Bool = false) -> (String, Date)? {
        NSApp.activate(ignoringOtherApps: true)
        let alert = NSAlert()
        alert.messageText = title
        alert.informativeText = info
        alert.addButton(withTitle: "OK")
        alert.addButton(withTitle: "Отмена")
        let field = NSTextField(frame: NSRect(x: 0, y: 0, width: 240, height: 24))
        field.stringValue = text
        var picker: NSDatePicker?
        if timeField {
            let box = NSView(frame: NSRect(x: 0, y: 0, width: 240, height: 60))
            let p = NSDatePicker(frame: NSRect(x: 0, y: 34, width: 120, height: 26))
            p.datePickerStyle = .textFieldAndStepper
            p.datePickerElements = .hourMinute
            p.dateValue = Date().addingTimeInterval(600)
            box.addSubview(p)
            field.frame = NSRect(x: 0, y: 0, width: 240, height: 24)
            box.addSubview(field)
            alert.accessoryView = box
            picker = p
        } else {
            alert.accessoryView = field
        }
        alert.window.initialFirstResponder = field
        guard alert.runModal() == .alertFirstButtonReturn else { return nil }
        var when = Date()
        if let p = picker {
            let cal = Calendar.current
            let hm = cal.dateComponents([.hour, .minute], from: p.dateValue)
            when = cal.nextDate(after: Date(), matching: hm, matchingPolicy: .nextTime) ?? Date()
        }
        return (field.stringValue.trimmingCharacters(in: .whitespaces), when)
    }

    @objc func editUserName() {
        if let (s, _) = ask("Как тебя зовут?", "Кот будет звать тебя по имени.", text: Prefs.userName) {
            Prefs.userName = s
            if !s.isEmpty { showMessage("\(s)! Красивое имя. Мяу", for: 4); play("Purr") }
            refreshUI()
        }
    }

    @objc func editCatName() {
        if let (s, _) = ask("Как зовут кота?", "Имя покажется под котом (включи в меню).", text: Prefs.catName) {
            Prefs.catName = s
            if !s.isEmpty { Prefs.showCatName = true; showMessage("Теперь я \(s)! Мяу :3", for: 4) }
            refreshUI()
        }
    }

    @objc func editNote() {
        if let (s, _) = ask("Закрепить заметку", "Будет висеть над котом. Пусто — убрать.", text: Prefs.fixedNote) {
            Prefs.fixedNote = s
            refreshUI()
        }
    }

    @objc func addReminder() {
        if let (s, when) = ask("Напоминание", "Кот мяукнет в выбранное время.", text: "", timeField: true), !s.isEmpty {
            var r = Prefs.reminders
            r.append(Reminder(t: when, m: s))
            r.sort { $0.t < $1.t }
            Prefs.reminders = r
            let df = DateFormatter(); df.dateFormat = "HH:mm"
            showMessage("Напомню в \(df.string(from: when)): \(s)", for: 4)
            refreshUI()
        }
    }

    @objc func removeReminder(_ sender: NSMenuItem) {
        var r = Prefs.reminders
        if sender.tag < r.count { r.remove(at: sender.tag) }
        Prefs.reminders = r
        refreshUI()
    }

    // MARK: custom coat

    @objc func importCoat() {
        NSApp.activate(ignoringOtherApps: true)
        let panel = NSOpenPanel()
        panel.allowedContentTypes = [.png, .json]
        panel.message = "JSON с comnyang.com/showcase или PNG-шаблон \(GRID_W)×\(GRID_H) (кратный размер)"
        guard panel.runModal() == .OK, let url = panel.url else { return }
        importCoat(from: url)
    }

    func importCoat(from url: URL) {
        let ok: Bool
        if url.pathExtension.lowercased() == "json" {
            ok = importComnyangJSON(url)
        } else {
            ok = importTemplatePNG(url)
        }
        if ok {
            Prefs.coatType = "custom"
            coat.loadCustom()
            showMessage("Новый окрас! Как тебе? Мяу", for: 4)
            refreshUI()
        }
    }

    func saveOverrides(_ ov: [Int: NSColor]) {
        var dict: [String: String] = [:]
        for (idx, c) in ov { dict["\(idx % GRID_W),\(idx / GRID_W)"] = hexFromColor(c) }
        Prefs.customPattern = try? JSONEncoder().encode(dict)
    }

    func importTemplatePNG(_ url: URL) -> Bool {
        guard let data = try? Data(contentsOf: url), let rep = NSBitmapImageRep(data: data) else { return false }
        guard rep.pixelsWide % GRID_W == 0, rep.pixelsHigh % GRID_H == 0,
              rep.pixelsWide / GRID_W == rep.pixelsHigh / GRID_H else {
            alertInfo("Не тот PNG", "Нужен шаблон \(GRID_W)×\(GRID_H) (или кратный). " +
                      "PNG с comnyang.com — это просто картинка их кота; с сайта бери JSON, его я понимаю.")
            return false
        }
        let k = rep.pixelsWide / GRID_W
        var ov: [Int: NSColor] = [:]
        for y in 0..<GRID_H {
            for x in 0..<GRID_W {
                guard let c = rep.colorAt(x: x*k + k/2, y: y*k + k/2), c.alphaComponent > 0.5 else { continue }
                ov[y*GRID_W + x] = c.usingColorSpace(.sRGB) ?? c
            }
        }
        saveOverrides(ov)
        return true
    }

    // maps a comnyang showcase pattern (their part-based grid) onto our cat semantically
    func importComnyangJSON(_ url: URL) -> Bool {
        guard let data = try? Data(contentsOf: url),
              let root = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            alertInfo("Не читается", "Это не похоже на JSON с comnyang.com/showcase.")
            return false
        }
        let pattern = (root["pattern_json"] as? [String: Any])
            ?? ((root["preset"] as? [String: Any])?["pattern"] as? [String: Any])
        guard let pat = pattern, let baseHex = pat["baseColor"] as? String,
              let base = colorFromHex(baseHex) else {
            alertInfo("Не читается", "В файле нет pattern/baseColor — это точно JSON из showcase?")
            return false
        }

        func partColors(_ keys: [String]) -> [String] {
            keys.flatMap { (pat[$0] as? [[String: Any]]) ?? [] }.compactMap { ($0["color"] as? String)?.uppercased() }
        }
        func dominant(_ arr: [String]) -> NSColor? {
            var counts: [String: Int] = [:]
            for c in arr { counts[c, default: 0] += 1 }
            guard let top = counts.max(by: { $0.value < $1.value }) else { return nil }
            return colorFromHex(top.key)
        }
        // "pinkest" minority color in the head part = nose
        func noseColor(_ arr: [String]) -> NSColor? {
            var counts: [String: Int] = [:]
            for c in arr { counts[c, default: 0] += 1 }
            let candidates = counts.filter { $0.value <= max(4, arr.count / 8) }.keys.compactMap(colorFromHex)
            return candidates.max { ($0.redComponent - $0.greenComponent) < ($1.redComponent - $1.greenComponent) }
        }

        let hsb = base.usingColorSpace(.sRGB) ?? base
        let stripe = NSColor(hue: hsb.hueComponent, saturation: hsb.saturationComponent,
                             brightness: hsb.brightnessComponent < 0.5
                                 ? min(1, hsb.brightnessComponent + 0.14)
                                 : max(0, hsb.brightnessComponent - 0.14),
                             alpha: 1)
        let headArr = partColors(["head"])
        let earC   = dominant(partColors(["earL", "earR"]))
        let tailC  = dominant(partColors(["tail"]))
        let pawC   = dominant(partColors(["legFl", "legFr", "legRl", "legRr"])) ?? base
        let bellyC = dominant(partColors(["body"])) ?? base
        let muzzC  = dominant(headArr) ?? base
        let noseC  = noseColor(headArr)

        var ov: [Int: NSColor] = [:]
        for frame in [FRAME_TAIL_DOWN, FRAME_TAIL_UP, FRAME_KNEAD_0, FRAME_KNEAD_1] {
        for (y, row) in frame.enumerated() {
            for (x, ch) in row.enumerated() {
                let idx = y*GRID_W + x
                if ov[idx] != nil { continue }
                switch ch {
                case "b":
                    if y <= 4 { ov[idx] = earC ?? base }
                    else if x >= 18 && y >= 12 { ov[idx] = tailC ?? base }
                    else { ov[idx] = base }
                case "s":
                    ov[idx] = (x >= 18 && y >= 12) ? (tailC ?? stripe) : stripe
                case "w":
                    if y == 17 { ov[idx] = pawC }
                    else if y >= 13 { ov[idx] = bellyC }
                    else { ov[idx] = muzzC }
                case "p":
                    if y > 5, let n = noseC { ov[idx] = n }  // nose only; inner ears keep pink
                default: break
                }
            }
        }
        }
        saveOverrides(ov)

        // adopt the cat's name from the file
        let importedName = (root["cat_name"] as? String)
            ?? ((root["preset"] as? [String: Any])?["catName"] as? String) ?? ""
        if !importedName.isEmpty {
            Prefs.catName = importedName
            Prefs.showCatName = true
            showMessage("Теперь я \(importedName)! Мяу :3", for: 5)
        }
        return true
    }

    func alertInfo(_ title: String, _ text: String) {
        NSApp.activate(ignoringOtherApps: true)
        let a = NSAlert()
        a.messageText = title
        a.informativeText = text
        a.runModal()
    }

    @objc func exportTemplate() {
        NSApp.activate(ignoringOtherApps: true)
        let panel = NSSavePanel()
        panel.allowedContentTypes = [.png]
        panel.nameFieldStringValue = "comnyan-template.png"
        panel.message = "Раскрась и загрузи обратно через «Свой окрас (PNG)…»"
        guard panel.runModal() == .OK, let url = panel.url else { return }
        let k = 10  // upscale so it's editable
        guard let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: GRID_W*k, pixelsHigh: GRID_H*k,
                                         bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
                                         colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0) else { return }
        NSGraphicsContext.saveGraphicsState()
        let gc = NSGraphicsContext(bitmapImageRep: rep)
        NSGraphicsContext.current = gc
        if let ctx = gc?.cgContext {
            for (row, line) in baseFrame().enumerated() {
                for (col, ch) in line.enumerated() {
                    guard let c = coat.cellColor(col, row, ch, hot: false) else { continue }
                    c.setFill()
                    ctx.fill(CGRect(x: CGFloat(col*k), y: CGFloat((GRID_H - 1 - row)*k),
                                    width: CGFloat(k), height: CGFloat(k)))
                }
            }
        }
        NSGraphicsContext.restoreGraphicsState()
        try? rep.representation(using: .png, properties: [:])?.write(to: url)
    }

    // MARK: behaviors

    func noteKeyActivity(now: Date) {
        if secondsSince(.keyDown) < 0.04 { keyEvents.append(now) }
        keyEvents.removeAll { now.timeIntervalSince($0) > 2 }
        let kps = Double(keyEvents.count) / 2
        if kps >= 5 {
            if hotSince == nil { hotSince = now }
            if now.timeIntervalSince(hotSince!) > 1.5 { overheated = true }
        } else if kps < 2 {
            hotSince = nil
            overheated = false
        }
    }

    // MARK: hunt

    func huntActive(_ now: Date) -> Bool { huntStalkUntil > now || pounce != nil }

    func trackMouseForHunt(now: Date) {
        let m = NSEvent.mouseLocation
        let dx = m.x - prevMouse.x, dy = m.y - prevMouse.y
        prevMouse = m
        guard Prefs.huntEnabled, !catView.dragging, !peeking else { return }

        // count direction reversals: a shake is several of them within a short window
        if abs(dx) > 4 {
            let dir = dx > 0 ? 1 : -1
            if lastDirX != 0, dir != lastDirX { reversalsX.append(now) }
            lastDirX = dir
        }
        if abs(dy) > 4 {
            let dir = dy > 0 ? 1 : -1
            if lastDirY != 0, dir != lastDirY { reversalsY.append(now) }
            lastDirY = dir
        }
        reversalsX.removeAll { now.timeIntervalSince($0) > 0.8 }
        reversalsY.removeAll { now.timeIntervalSince($0) > 0.8 }

        if pounce == nil, huntStalkUntil <= now, now > huntCooldownUntil,
           max(reversalsX.count, reversalsY.count) >= 4,
           hypot(m.x - window.frame.midX, m.y - window.frame.midY) > 120 {
            huntStalkUntil = now.addingTimeInterval(0.6)
            pounceCount = 0
            reversalsX.removeAll(); reversalsY.removeAll()
        }

        // stalk finished -> first pounce
        if pounce == nil, huntStalkUntil != .distantPast, now >= huntStalkUntil {
            huntStalkUntil = .distantPast
            startPounce(now: now, toward: m)
        }

        if let p = pounce {
            let t = CGFloat(now.timeIntervalSince(p.start)) / 0.35
            if t >= 1 {
                window.setFrameOrigin(p.to)
                pounce = nil
                catView.jelly = 0.12
                // keep chasing while the cursor is still far away
                let d = hypot(m.x - window.frame.midX, m.y - window.frame.midY)
                if pounceCount < 3, d > 150 {
                    startPounce(now: now, toward: m)
                } else {
                    Prefs.pos = window.frame.origin
                    huntCooldownUntil = now.addingTimeInterval(8)
                    catView.jumpStarted = now
                }
            } else {
                let e = t * t * (3 - 2 * t)  // smoothstep
                let x = p.from.x + (p.to.x - p.from.x) * e
                let y = p.from.y + (p.to.y - p.from.y) * e + sin(t * .pi) * 42
                window.setFrameOrigin(NSPoint(x: x, y: y))
            }
        }
    }

    func startPounce(now: Date, toward m: NSPoint) {
        let from = window.frame.origin
        var target = NSPoint(x: m.x - window.frame.width/2,
                             y: m.y - catView.marginBottom - catView.catH*0.7)
        let dx = target.x - from.x, dy = target.y - from.y
        let dist = hypot(dx, dy)
        let maxD: CGFloat = 320
        if dist > maxD { target = NSPoint(x: from.x + dx/dist*maxD, y: from.y + dy/dist*maxD) }
        if let scr = window.screen ?? NSScreen.main {
            let v = scr.visibleFrame
            target.x = max(v.minX - 20, min(target.x, v.maxX - window.frame.width + 20))
            target.y = max(v.minY - 4, min(target.y, v.maxY - window.frame.height))
        }
        pounce = (from, target, now)
        pounceCount += 1
    }

    // MARK: walks — every few minutes the cat strolls a bit along the screen

    func doWalk(now: Date) {
        if now >= nextWalkAt {
            nextWalkAt = now.addingTimeInterval(Double.random(in: 240...600))
            if catView.state == .idle, !peeking, pounce == nil, !catView.dragging, walkHopsLeft == 0,
               let v = currentScreen()?.visibleFrame {
                let target = window.frame.origin.x + CGFloat.random(in: 90...240) * (Bool.random() ? 1 : -1)
                let clamped = max(v.minX - 10, min(target, v.maxX - window.frame.width + 10))
                let total = clamped - window.frame.origin.x
                if abs(total) > 50 {
                    walkHopsLeft = 3
                    walkStepX = total / 3
                    catView.tailUpUntil = now.addingTimeInterval(2)
                }
            }
        }
        if walkHop == nil, walkHopsLeft > 0 {
            if catView.dragging || pounce != nil { walkHopsLeft = 0; return }
            let from = window.frame.origin
            walkHop = (from, NSPoint(x: from.x + walkStepX, y: from.y), now)
        }
        if let h = walkHop {
            if catView.dragging { walkHop = nil; walkHopsLeft = 0; return }
            let t = CGFloat(now.timeIntervalSince(h.start)) / 0.38
            if t >= 1 {
                window.setFrameOrigin(h.to)
                walkHop = nil
                walkHopsLeft -= 1
                if walkHopsLeft == 0 { Prefs.pos = window.frame.origin }
            } else {
                let e = t * t * (3 - 2 * t)
                let x = h.from.x + (h.to.x - h.from.x) * e
                let y = h.from.y + sin(t * .pi) * 13
                window.setFrameOrigin(NSPoint(x: x, y: y))
            }
        }
    }

    // MARK: agent (Claude Code hooks -> ~/.comnyan/agent)

    func checkAgentFile() {
        guard let attrs = try? FileManager.default.attributesOfItem(atPath: agentFile),
              let mtime = attrs[.modificationDate] as? Date,
              let content = try? String(contentsOfFile: agentFile, encoding: .utf8) else {
            agentThinking = false
            return
        }
        let word = content.trimmingCharacters(in: .whitespacesAndNewlines)
        let age = Date().timeIntervalSince(mtime)
        let wasThinking = agentThinking
        agentThinking = (word == "thinking" && age < 1800)
        if wasThinking, !agentThinking, word == "done", age < 120, lastAgentState == "thinking" {
            showMessage(name("агент закончил! Мяу!"), for: 6)
            catView.jumpStarted = Date()
            play("Glass")
        }
        lastAgentState = word
    }

    // MARK: peek (manual: drag the cat past a screen edge, click to pop back out)

    func currentScreen() -> NSScreen? {
        window.screen
            ?? NSScreen.screens.first { $0.frame.intersects(window.frame) }
            ?? NSScreen.main
    }

    // after a drag: if the cat hangs off a screen edge, tuck it in; otherwise just settle
    func settleAfterDrag() {
        guard let v = currentScreen()?.frame else { return }
        let catLeft = window.frame.minX + catView.marginX
        let catRight = window.frame.maxX - catView.marginX
        if catRight - v.maxX > catView.catW * 0.22 {
            peekTo(right: true, frame: v)
        } else if v.minX - catLeft > catView.catW * 0.22 {
            peekTo(right: false, frame: v)
        } else {
            peeking = false
            Prefs.pos = window.frame.origin
        }
    }

    func peekTo(right: Bool, frame v: NSRect) {
        peeking = true
        let visible = catView.catW * 0.38
        let x = right
            ? v.maxX - catView.marginX - visible
            : v.minX - (window.frame.width - catView.marginX - visible)
        window.setFrameOrigin(NSPoint(x: x, y: window.frame.origin.y))
        Prefs.pos = window.frame.origin
        play("Pop")
    }

    @objc func peekNearestEdge() {
        guard let v = currentScreen()?.frame else { return }
        peekTo(right: window.frame.midX >= v.midX, frame: v)
        refreshUI()
    }

    @objc func unpeek() {
        peeking = false
        guard let v = currentScreen()?.frame else { return }
        let x = window.frame.midX >= v.midX
            ? v.maxX - catView.marginX - catView.catW - 8
            : v.minX + 8 - catView.marginX
        window.setFrameOrigin(NSPoint(x: x, y: window.frame.origin.y))
        Prefs.pos = window.frame.origin
        catView.jumpStarted = Date()
        meow()
        refreshUI()
    }

    // MARK: misc

    func meow() {
        showMessage(["Мяу!", "Мррр~", "Мяяяу", "Ня!", ":3"].randomElement()!, for: 2)
        play("Pop")
    }

    func play(_ name: String) {
        guard Prefs.sounds else { return }
        NSSound(named: name)?.play()
    }

    func showMessage(_ text: String, for seconds: Double) {
        message = text
        messageUntil = Date().addingTimeInterval(seconds)
    }

    // MARK: main tick

    func tick() {
        let now = Date()
        tickCount += 1
        noteKeyActivity(now: now)
        trackMouseForHunt(now: now)
        catView.tick(now: now)

        // stretch reminder
        if Prefs.stretchMin > 0, stretchActiveUntil < now,
           now.timeIntervalSince(lastStretchAt) > Double(Prefs.stretchMin) * 60 {
            stretchActiveUntil = now.addingTimeInterval(20)
            lastStretchAt = now
            showMessage(name("потянись со мной! 🧘"), for: 20)
            play("Pop")
        }
        if stretchActiveUntil < now, messageUntil > now, message.hasSuffix("🧘") {
            messageUntil = now
        }

        // pomodoro
        if let end = pomoEnd, now >= end {
            if pomoIsBreak {
                pomoEnd = Date().addingTimeInterval(Double(pomoWork) * 60)
                pomoIsBreak = false
                showMessage(name("перерыв окончен — за работу!"), for: 5)
                play("Glass")
            } else {
                pomoEnd = Date().addingTimeInterval(Double(pomoBreak) * 60)
                pomoIsBreak = true
                showMessage(name("\(pomoWork) минут готово! Перерыв 🐾"), for: 6)
                play("Glass")
                catView.jumpStarted = now
            }
            refreshUI()
        }

        // reminders
        var rems = Prefs.reminders
        var fired = false
        for (i, r) in rems.enumerated().reversed() where now >= r.t {
            showMessage(name("напоминаю: \(r.m) 🐾"), for: 20)
            play("Purr")
            catView.jumpStarted = now
            rems.remove(at: i)
            fired = true
        }
        if fired { Prefs.reminders = rems; refreshUI() }

        // agent file — every 0.5 s
        if tickCount % 15 == 0 { checkAgentFile() }

        doWalk(now: now)

        // time of day + holidays — every 2 s
        if tickCount % 60 == 0 {
            let p = dayPeriod(now)
            nightNow = p == 0
            if p != lastPeriod {
                lastPeriod = p
                if p == 1 {
                    showMessage(name("утро! Потянемся ☀️"), for: 12)
                    stretchActiveUntil = now.addingTimeInterval(12)
                    play("Pop")
                } else if p == 0 {
                    showMessage(name("уже поздно… 🌙"), for: 8)
                }
                computeHat()
            }
        }

        updateBubble(now: now)
    }

    func updateBubble(now: Date) {
        var text: String?
        if messageUntil > now {
            text = message
        } else if !peeking {
            var parts: [String] = []
            if !Prefs.fixedNote.isEmpty { parts.append("📌 " + Prefs.fixedNote) }
            if let end = pomoEnd {
                let left = max(0, Int(end.timeIntervalSince(now)))
                parts.append(String(format: "%@ %02d:%02d", pomoIsBreak ? "☕️" : "🍅", left/60, left%60))
            }
            if !parts.isEmpty { text = parts.joined(separator: "  ·  ") }
        }
        guard let t = text else {
            if bubbleWindow.isVisible { bubbleWindow.orderOut(nil) }
            return
        }
        if bubbleView.text != t {
            bubbleView.text = t
            let size = BubbleView.size(for: t)
            bubbleView.frame = NSRect(origin: .zero, size: size)
            bubbleWindow.setContentSize(size)
        }
        let wf = window.frame
        let size = bubbleWindow.frame.size
        var x = wf.midX - size.width/2
        let y = wf.maxY - 4
        if let scr = window.screen ?? NSScreen.main {
            x = max(scr.visibleFrame.minX + 4, min(x, scr.visibleFrame.maxX - size.width - 4))
        }
        bubbleWindow.setFrameOrigin(NSPoint(x: x, y: y))
        if !bubbleWindow.isVisible { bubbleWindow.orderFrontRegardless() }
    }
}

extension NSMenu {
    func addItem(withSubmenu submenu: NSMenu, title: String) {
        let it = NSMenuItem(title: title, action: nil, keyEquivalent: "")
        it.submenu = submenu
        addItem(it)
    }
}
// MARK: - main

let app = NSApplication.shared
let controller = Controller()
app.delegate = controller
app.setActivationPolicy(.accessory)
app.run()
