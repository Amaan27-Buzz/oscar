use tauri::WebviewWindow;

pub const COMPACT: (f64, f64) = (132., 148.);
pub const INTERACTION: (f64, f64) = (432., 384.);

fn placement(
    old: (f64, f64, f64, f64),
    area: (f64, f64, f64, f64),
    size: (f64, f64),
    edge: bool,
) -> (f64, f64) {
    let (left, top, width, height) = area;
    let x = if edge {
        left + width - size.0 - 18.
    } else {
        old.0 + old.2 - size.0
    };
    let y = if edge {
        top + height - size.1 - 18.
    } else {
        old.1 + old.3 - size.1
    };
    (
        x.clamp(left, (left + width - size.0).max(left)),
        y.clamp(top, (top + height - size.1).max(top)),
    )
}

pub fn resize(window: &WebviewWindow, size: (f64, f64), edge: bool) -> Result<(), String> {
    let scale = window
        .scale_factor()
        .map_err(|_| "window scale unavailable")?;
    let old = window
        .outer_position()
        .map_err(|_| "window position unavailable")?
        .to_logical::<f64>(scale);
    let old_size = window
        .inner_size()
        .map_err(|_| "window size unavailable")?
        .to_logical::<f64>(scale);
    let monitor = window
        .current_monitor()
        .map_err(|_| "monitor unavailable")?
        .ok_or("monitor unavailable")?;
    let area = monitor.work_area();
    let origin = area.position.to_logical::<f64>(scale);
    let extent = area.size.to_logical::<f64>(scale);
    let size = (size.0.min(extent.width), size.1.min(extent.height));
    let position = placement(
        (old.x, old.y, old_size.width, old_size.height),
        (origin.x, origin.y, extent.width, extent.height),
        size,
        edge,
    );
    window
        .set_size(tauri::LogicalSize::new(size.0, size.1))
        .map_err(|_| "presence size unavailable")?;
    window
        .set_position(tauri::LogicalPosition::new(position.0, position.1))
        .map_err(|_| "presence position unavailable")?;
    Ok(())
}

#[derive(serde::Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Action {
    Hide,
    Pin,
    Float,
    Edge,
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn anchor_and_clamp_to_work_area_at_each_scale() {
        for scale in [1., 1.25, 1.5] {
            let area = (-1920. / scale, 0., 1920. / scale, 1040. / scale);
            let old = (-150., 400., 132., 148.);
            let next = placement(old, area, INTERACTION, false);
            assert_eq!(next.0 + INTERACTION.0, old.0 + old.2);
            assert_eq!(next.1 + INTERACTION.1, old.1 + old.3);
            let edge = placement(old, area, COMPACT, true);
            assert_eq!(edge.0 + COMPACT.0, -18.);
            assert_eq!(edge.1 + COMPACT.1, area.3 - 18.);
            let outside = placement((5000., 5000., 132., 148.), area, INTERACTION, false);
            assert!(outside.0 + INTERACTION.0 <= area.0 + area.2);
            assert!(outside.1 + INTERACTION.1 <= area.3);
        }
        assert!(serde_json::from_str::<Action>("\"shell\"").is_err());
    }
}
