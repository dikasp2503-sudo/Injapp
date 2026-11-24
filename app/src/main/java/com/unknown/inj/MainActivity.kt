package com.unknown.inj

import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import kotlin.concurrent.thread

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        if (!Python.isStarted()) Python.start(AndroidPlatform(this))

        val etProxy    = findViewById<EditText>(R.id.etProxyPath)
        val etEndpoint = findViewById<EditText>(R.id.etEndpoint)
        val etCount    = findViewById<EditText>(R.id.etCount)
        val btn        = findViewById<Button>(R.id.btnRun)
        val tvOut      = findViewById<TextView>(R.id.tvOut)

        btn.setOnClickListener {
            tvOut.text = "jalan..."
            val mod = Python.getInstance().getModule("gmail_injector")
            thread {
                val res = mod.callAttr(
                    "android_run",
                    etProxy.text.toString(),
                    etEndpoint.text.toString(),
                    etCount.text.toString().toIntOrNull() ?: 5
                ).toString()
                runOnUiThread { tvOut.text = res }
            }
        }
    }
}
