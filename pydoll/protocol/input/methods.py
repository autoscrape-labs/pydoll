from enum import Enum


class InputMethod(str, Enum):
    CANCEL_DRAGGING = 'Input.cancelDragging'
    DISPATCH_KEY_EVENT = 'Input.dispatchKeyEvent'
    DISPATCH_MOUSE_EVENT = 'Input.dispatchMouseEvent'
    DISPATCH_TOUCH_EVENT = 'Input.dispatchTouchEvent'
    SET_IGNORE_INPUT_EVENTS = 'Input.setIgnoreInputEvents'
    DISPATCH_DRAG_EVENT = 'Input.dispatchDragEvent'
    EMULATE_TOUCH_FROM_MOUSE_EVENT = 'Input.emulateTouchFromMouseEvent'
    IME_SET_COMPOSITION = 'Input.imeSetComposition'
    INSERT_TEXT = 'Input.insertText'
    SET_INTERCEPT_DRAGS = 'Input.setInterceptDrags'
    SYNTHESIZE_PINCH_GESTURE = 'Input.synthesizePinchGesture'
    SYNTHESIZE_SCROLL_GESTURE = 'Input.synthesizeScrollGesture'
    SYNTHESIZE_TAP_GESTURE = 'Input.synthesizeTapGesture'
